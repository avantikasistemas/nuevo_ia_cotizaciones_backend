from werkzeug.security import check_password_hash
from datetime import datetime, timedelta, timezone
from Utils.tools import Tools, CustomException
from Utils.querys import Querys
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET", "cambia_esto_en_produccion")
ALGORITHM  = "HS256"
EXPIRE_HRS = 15


class Auth:

    def __init__(self, db):
        self.tools  = Tools()
        self.querys = Querys(db)

    def login(self, data: dict):
        usuario  = str(data.get("usuario", "")).strip()
        password = str(data.get("password", "")).strip()

        if not usuario or not password:
            raise CustomException("Usuario y contraseña son requeridos.", 400)

        # Validación 1: dbo.ia_usuarios (clave cifrada)
        row_ia = self.querys.auth_get_ia_usuario(usuario)

        if not row_ia:
            raise CustomException("Credenciales incorrectas. El usuario no está registrado en el sistema IA.", 401)
        if row_ia.estado == 0:
            raise CustomException("Usuario inactivo en el sistema IA. Contacte al administrador.", 403)
        if not check_password_hash(row_ia.clave, password):
            raise CustomException("Credenciales incorrectas. La contraseña no coincide en el sistema IA.", 401)

        # Validación 2: tabla usuarios original (clave en texto plano)
        row_dms = self.querys.auth_get_dms_usuario(usuario)

        if not row_dms:
            raise CustomException("El usuario no existe en el sistema DMS.", 401)
        if row_dms.bloqueado == 'S':
            raise CustomException("Usuario bloqueado en el sistema DMS. Contacte al administrador.", 403)
        if row_dms.clave != password:
            raise CustomException("Credenciales incorrectas. La contraseña no coincide en el sistema DMS.", 401)

        nombre_completo = str(row_dms.des_usuario or row_ia.usuario).strip()
        self.querys.auth_update_conexion(row_ia.id)

        expires_at = datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HRS)
        payload = {
            "sub":        row_ia.usuario,
            "id":         row_ia.id,
            "rol":        row_ia.rol,
            "nombre_rol": row_ia.nombre_rol,
            "name":       nombre_completo,
            "exp":        expires_at,
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return self.tools.output(200, "Login exitoso", {
            "access_token": token,
            "token_type":   "bearer",
            "expires_in":   EXPIRE_HRS * 3600,
            "user": {
                "id":         row_ia.id,
                "usuario":    row_ia.usuario,
                "name":       nombre_completo,
                "rol":        row_ia.rol,
                "nombre_rol": row_ia.nombre_rol,
            },
        })

    def me(self, data: dict):
        token = str(data.get("token", "")).strip()
        if not token:
            raise CustomException("Token requerido.", 400)

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise CustomException("Token expirado. Inicie sesión nuevamente.", 401)
        except jwt.InvalidTokenError:
            raise CustomException("Token inválido.", 401)

        row = self.querys.auth_get_me(payload["id"])
        if not row or row.estado == 0:
            raise CustomException("Usuario no encontrado o inactivo.", 401)

        return self.tools.output(200, "Perfil obtenido", {
            "id":         row.id,
            "usuario":    row.usuario,
            "name":       payload.get("name", row.usuario),
            "rol":        row.rol,
            "nombre_rol": row.nombre_rol,
        })
