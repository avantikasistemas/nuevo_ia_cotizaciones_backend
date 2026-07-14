import requests as http
import threading
import traceback
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from Utils.tools import CustomException

EMAIL_CUENTA  = "cotizaciones@avantika.com.co"
CARPETA_INBOX = "Inbox"
CARPETA_NOMBRE = "Solicitudes"


class GraphService:
    """Singleton que gestiona el token de Microsoft Graph con dos capas de caché:
    1. En memoria  → 0 latencia mientras el proceso vive.
    2. BD (dbo.ia_graph_token) → sobrevive reinicios y es compartida entre workers.
    Solo llama a Azure cuando ambas capas están vacías o expiradas.
    """

    _instance       = None
    _singleton_lock = threading.Lock()

    def __init__(self):
        self._token_lock   = threading.Lock()
        self._access_token = None
        self._expires_at   = None          # datetime con timezone UTC
        self._folder_cache = {}            # "email:carpeta" → folder_id

    # ── Singleton ────────────────────────────────────────────────────────
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── Credenciales ─────────────────────────────────────────────────────
    def _get_credentials(self, db):
        rows = db.execute(text(
            "SELECT nombre, valor FROM intranet_graph_credenciales WHERE estado = 1"
        )).fetchall()
        return {r.nombre: r.valor for r in rows}

    # ── Token con caché de 2 capas ────────────────────────────────────────
    def get_access_token(self, db):
        with self._token_lock:
            now    = datetime.now(timezone.utc)
            buffer = timedelta(minutes=5)

            # 1. Caché en memoria
            if self._access_token and self._expires_at and self._expires_at > now + buffer:
                return self._access_token

            # 2. Caché en BD
            row = db.execute(text("""
                SELECT TOP 1 access_token, expires_at
                FROM dbo.ia_graph_token
                WHERE expires_at > DATEADD(MINUTE, 5, GETUTCDATE())
                ORDER BY created_at DESC
            """)).fetchone()

            if row:
                exp = row.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                self._access_token = row.access_token
                self._expires_at   = exp
                return self._access_token

            # 3. Obtener token nuevo de Azure
            creds     = self._get_credentials(db)
            token_url = f"{creds['MICROSOFT_URL']}{creds['MICROSOFT_TENANT_ID']}/oauth2/v2.0/token"

            try:
                resp = http.post(token_url, data={
                    "client_id":     creds["MICROSOFT_CLIENT_ID"],
                    "client_secret": creds["MICROSOFT_CLIENT_SECRET"],
                    "scope":         "https://graph.microsoft.com/.default",
                    "grant_type":    "client_credentials",
                }, timeout=15)
                resp.raise_for_status()
            except Exception as e:
                traceback.print_exc()
                raise CustomException(f"Error obteniendo token de Azure: {e}", 500)

            data       = resp.json()
            token      = data["access_token"]
            expires_in = int(data.get("expires_in", 3600))
            expires_at = now + timedelta(seconds=expires_in)

            # Guardar en BD (solo 1 fila)
            try:
                db.execute(text("DELETE FROM dbo.ia_graph_token"))
                db.execute(text("""
                    INSERT INTO dbo.ia_graph_token (access_token, expires_at)
                    VALUES (:token, :expires_at)
                """), {"token": token, "expires_at": expires_at})
                db.commit()
            except Exception:
                traceback.print_exc()
                # No falla la petición si no puede guardar en BD

            self._access_token = token
            self._expires_at   = expires_at
            return token

    # ── Helpers internos ─────────────────────────────────────────────────
    def _headers(self, token):
        return {
            "Authorization":    f"Bearer {token}",
            "Accept":           "application/json",
            "ConsistencyLevel": "eventual",
        }

    def _get_folder_id(self, db, graph_url, email, carpeta):
        cache_key = f"{email}:{carpeta}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        token = self.get_access_token(db)
        url   = f"{graph_url}{email}/mailFolders/{CARPETA_INBOX}/childFolders"
        resp  = http.get(url, headers=self._headers(token), timeout=15)
        resp.raise_for_status()

        folder_id = next(
            (f["id"] for f in resp.json().get("value", []) if f["displayName"] == carpeta),
            None
        )
        if folder_id:
            self._folder_cache[cache_key] = folder_id
        return folder_id

    # ── Listar correos ────────────────────────────────────────────────────
    def list_emails(self, db, page=1, limit=20, search="",
                    leidos=None, date_from="", date_to="", sort_order="desc"):
        """
        leidos: None = todos, True = solo leídos, False = solo no leídos
        sort_order: 'desc' (más recientes) | 'asc' (más antiguos)
        date_from / date_to: 'YYYY-MM-DD'
        """
        creds     = self._get_credentials(db)
        graph_url = creds["MICROSOFT_URL_GRAPH"]
        token     = self.get_access_token(db)
        folder_id = self._get_folder_id(db, graph_url, EMAIL_CUENTA, CARPETA_NOMBRE)

        if not folder_id:
            raise CustomException(f"No se encontró la carpeta '{CARPETA_NOMBRE}' en el buzón.", 404)

        # Exchange Online NO soporta $search combinado con $filter, $orderby ni $skip.
        # Con búsqueda: traemos 50 resultados por relevancia sin paginación.
        # Sin búsqueda: paginación real con $skip, $orderby y $filter completos.
        if search:
            params = {
                "$top":    50,
                "$select": "id,subject,from,receivedDateTime,hasAttachments,isRead,bodyPreview",
                "$search": f'"{search}"',
            }
        else:
            skip      = (page - 1) * limit
            orderby   = f"receivedDateTime {'desc' if sort_order == 'desc' else 'asc'}"
            filters   = []

            if leidos is True:
                filters.append("isRead eq true")
            elif leidos is False:
                filters.append("isRead eq false")

            if date_from:
                filters.append(f"receivedDateTime ge {date_from}T00:00:00Z")
            if date_to:
                filters.append(f"receivedDateTime le {date_to}T23:59:59Z")

            params = {
                "$top":     limit,
                "$skip":    skip,
                "$select":  "id,subject,from,receivedDateTime,hasAttachments,isRead,bodyPreview",
                "$orderby": orderby,
                "$count":   "true",
            }
            if filters:
                params["$filter"] = " and ".join(filters)

        url  = f"{graph_url}{EMAIL_CUENTA}/mailFolders/{folder_id}/messages"
        resp = http.get(url, headers=self._headers(token), params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        messages = data.get("value", [])

        if search:
            # Filtros del lado del servidor sobre los 50 resultados de búsqueda
            if leidos is True:
                messages = [m for m in messages if m.get("isRead", False)]
            elif leidos is False:
                messages = [m for m in messages if not m.get("isRead", True)]
            total = len(messages)
            pages = 1
            page  = 1
        else:
            total = data.get("@odata.count", len(messages))
            pages = max(1, -(-total // limit)) if total else 1

        items = [{
            "id":               m["id"],
            "asunto":           m.get("subject") or "(Sin asunto)",
            "remitente_nombre": m.get("from", {}).get("emailAddress", {}).get("name", ""),
            "remitente_email":  m.get("from", {}).get("emailAddress", {}).get("address", ""),
            "fecha":            m.get("receivedDateTime", ""),
            "tiene_adjuntos":   m.get("hasAttachments", False),
            "leido":            m.get("isRead", False),
            "preview":          m.get("bodyPreview", ""),
        } for m in messages]

        return {
            "items": items,
            "total": total,
            "page":  page,
            "limit": limit,
            "pages": pages,
        }

    # ── Detalle de un correo ──────────────────────────────────────────────
    def get_email_detail(self, db, message_id):
        creds     = self._get_credentials(db)
        graph_url = creds["MICROSOFT_URL_GRAPH"]
        token     = self.get_access_token(db)
        headers   = self._headers(token)

        url    = f"{graph_url}{EMAIL_CUENTA}/messages/{message_id}"
        params = {"$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,hasAttachments,isRead,body"}
        resp   = http.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        msg = resp.json()

        adjuntos = []
        if msg.get("hasAttachments"):
            att_url  = f"{graph_url}{EMAIL_CUENTA}/messages/{message_id}/attachments"
            att_resp = http.get(att_url, headers=headers, timeout=30)
            att_resp.raise_for_status()
            for a in att_resp.json().get("value", []):
                if not a.get("isInline", False):
                    adjuntos.append({
                        "id":           a.get("id"),
                        "nombre":       a.get("name"),
                        "tipo":         a.get("contentType"),
                        "tamano_bytes": a.get("size"),
                        "contenido_b64": a.get("contentBytes"),
                    })

        return {
            "id":               msg["id"],
            "asunto":           msg.get("subject") or "(Sin asunto)",
            "remitente_nombre": msg.get("from", {}).get("emailAddress", {}).get("name", ""),
            "remitente_email":  msg.get("from", {}).get("emailAddress", {}).get("address", ""),
            "destinatarios":    [r.get("emailAddress", {}) for r in msg.get("toRecipients", [])],
            "cc":               [r.get("emailAddress", {}) for r in msg.get("ccRecipients", [])],
            "fecha":            msg.get("receivedDateTime", ""),
            "tiene_adjuntos":   msg.get("hasAttachments", False),
            "leido":            msg.get("isRead", False),
            "cuerpo_html":      msg.get("body", {}).get("content", ""),
            "cuerpo_tipo":      msg.get("body", {}).get("contentType", "html"),
            "adjuntos":         adjuntos,
        }
