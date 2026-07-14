from Utils.tools import Tools, CustomException
from sqlalchemy import text, func, case, extract, and_, or_, Date, cast
from datetime import datetime, date
import traceback
import pytz

class Querys:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.query_params = dict()
        self.colombia_tz = pytz.timezone('America/Bogota')

    # ═══════════════════════════════════════════════════════════════
    #  IA_USUARIOS
    # ═══════════════════════════════════════════════════════════════

    def ia_usuarios_listar(self, page=1, limit=10, filtro=""):
        offset = (page - 1) * limit
        like   = f"%{filtro}%" if filtro else "%"
        try:
            total = self.db.execute(text("""
                SELECT COUNT(*)
                FROM dbo.ia_usuarios u
                JOIN dbo.ia_roles r    ON r.id  = u.rol
                LEFT JOIN usuarios du  ON du.usuario = u.usuario
                WHERE u.usuario      LIKE :f
                   OR du.des_usuario LIKE :f
            """), {"f": like}).scalar() or 0

            rows = self.db.execute(text("""
                SELECT
                    u.id,
                    u.usuario,
                    ISNULL(du.des_usuario, u.usuario) AS nombre_completo,
                    u.rol,
                    r.nombre  AS nombre_rol,
                    u.estado,
                    u.created_at,
                    u.fecha_ultima_conexion
                FROM dbo.ia_usuarios u
                JOIN dbo.ia_roles r    ON r.id  = u.rol
                LEFT JOIN usuarios du  ON du.usuario = u.usuario
                WHERE u.usuario      LIKE :f
                   OR du.des_usuario LIKE :f
                ORDER BY u.created_at DESC
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """), {"f": like, "offset": offset, "limit": limit}).fetchall()

            return {
                "items": [{
                    "id":                    r.id,
                    "usuario":               r.usuario,
                    "nombre_completo":       r.nombre_completo,
                    "rol":                   r.rol,
                    "nombre_rol":            r.nombre_rol,
                    "estado":                r.estado,
                    "created_at":            str(r.created_at),
                    "fecha_ultima_conexion": str(r.fecha_ultima_conexion) if r.fecha_ultima_conexion else None,
                } for r in rows],
                "total": total,
                "page":  page,
                "limit": limit,
                "pages": max(1, -(-total // limit)),
            }
        except CustomException:
            raise
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando ia_usuarios: {e}")

    def ia_usuarios_listar_dms(self, filtro=""):
        like = f"%{filtro}%" if filtro else "%"
        try:
            rows = self.db.execute(text("""
                SELECT usuario, des_usuario
                FROM usuarios
                WHERE bloqueado IS NULL
                  AND (usuario     LIKE :f
                    OR des_usuario LIKE :f)
                ORDER BY des_usuario
            """), {"f": like}).fetchall()
            return [{"usuario": r.usuario, "des_usuario": str(r.des_usuario or r.usuario).strip()} for r in rows]
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando usuarios DMS: {e}")

    def ia_usuarios_existe(self, usuario):
        try:
            return self.db.execute(text(
                "SELECT COUNT(*) FROM dbo.ia_usuarios WHERE usuario = :u"
            ), {"u": usuario}).scalar() or 0
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error verificando usuario: {e}")

    def ia_usuarios_crear(self, usuario, clave_hash, rol):
        try:
            self.db.execute(text("""
                INSERT INTO dbo.ia_usuarios (usuario, clave, rol, estado)
                VALUES (:usuario, :clave, :rol, 1)
            """), {"usuario": usuario, "clave": clave_hash, "rol": int(rol)})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error creando usuario: {e}")

    def ia_usuarios_actualizar(self, id_usuario, sets, params):
        try:
            self.db.execute(text(
                f"UPDATE dbo.ia_usuarios SET {', '.join(sets)} WHERE id = :id"
            ), params)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error actualizando usuario: {e}")

    def ia_usuarios_eliminar(self, id_usuario):
        try:
            self.db.execute(text(
                "DELETE FROM dbo.ia_usuarios WHERE id = :id"
            ), {"id": int(id_usuario)})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error eliminando usuario: {e}")

    # ═══════════════════════════════════════════════════════════════
    #  AUTH
    # ═══════════════════════════════════════════════════════════════

    def auth_get_ia_usuario(self, usuario):
        try:
            return self.db.execute(text("""
                SELECT u.id, u.usuario, u.clave, u.rol, u.estado, r.nombre AS nombre_rol
                FROM dbo.ia_usuarios u
                JOIN dbo.ia_roles    r ON r.id = u.rol
                WHERE u.usuario = :usuario
            """), {"usuario": usuario}).fetchone()
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando ia_usuario: {e}")

    def auth_get_dms_usuario(self, usuario):
        try:
            return self.db.execute(text("""
                SELECT usuario, clave, bloqueado, des_usuario
                FROM usuarios
                WHERE usuario = :usuario
            """), {"usuario": usuario}).fetchone()
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando usuario DMS: {e}")

    def auth_update_conexion(self, id_usuario):
        try:
            self.db.execute(text("""
                UPDATE dbo.ia_usuarios
                SET fecha_ultima_conexion = GETDATE(), updated_at = GETDATE()
                WHERE id = :id
            """), {"id": id_usuario})
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            raise CustomException(f"Error actualizando conexión: {e}")

    def auth_get_me(self, id_usuario):
        try:
            return self.db.execute(text("""
                SELECT u.id, u.usuario, u.rol, u.estado, r.nombre AS nombre_rol
                FROM dbo.ia_usuarios u
                JOIN dbo.ia_roles    r ON r.id = u.rol
                WHERE u.id = :id
            """), {"id": id_usuario}).fetchone()
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error consultando perfil: {e}")
