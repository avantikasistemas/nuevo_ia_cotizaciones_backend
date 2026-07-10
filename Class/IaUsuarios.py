from werkzeug.security import generate_password_hash
from Utils.tools import Tools, CustomException
from Utils.querys import Querys


class IaUsuarios:

    def __init__(self, db):
        self.tools  = Tools()
        self.querys = Querys(db)

    def listar(self, data: dict):
        page   = int(data.get("page", 1))
        limit  = int(data.get("limit", 10))
        filtro = str(data.get("filtro", "")).strip()
        result = self.querys.ia_usuarios_listar(page=page, limit=limit, filtro=filtro)
        return self.tools.output(200, "Usuarios obtenidos", result)

    def listar_dms(self, data: dict):
        filtro = str(data.get("filtro", "")).strip()
        items  = self.querys.ia_usuarios_listar_dms(filtro=filtro)
        return self.tools.output(200, "Usuarios DMS obtenidos", items)

    def crear(self, data: dict):
        usuario  = str(data.get("usuario", "")).strip()
        password = str(data.get("password", "")).strip()
        rol      = data.get("rol")

        if not usuario:
            raise CustomException("El campo usuario es requerido.", 400)
        if not password or len(password) < 6:
            raise CustomException("La contraseña debe tener al menos 6 caracteres.", 400)
        if not rol:
            raise CustomException("El campo rol es requerido.", 400)

        if self.querys.ia_usuarios_existe(usuario):
            raise CustomException(f"El usuario '{usuario}' ya está registrado en el sistema IA.", 409)

        clave_hash = generate_password_hash(password)
        self.querys.ia_usuarios_crear(usuario, clave_hash, rol)
        return self.tools.output(200, f"Usuario '{usuario}' creado correctamente.")

    def actualizar(self, data: dict):
        id_usuario = data.get("id")
        rol        = data.get("rol")
        estado     = data.get("estado")
        password   = str(data.get("password", "")).strip()

        if not id_usuario:
            raise CustomException("El campo id es requerido.", 400)

        sets   = []
        params = {"id": int(id_usuario)}

        if rol is not None:
            sets.append("rol = :rol")
            params["rol"] = int(rol)
        if estado is not None:
            sets.append("estado = :estado")
            params["estado"] = int(estado)
        if password:
            if len(password) < 6:
                raise CustomException("La contraseña debe tener al menos 6 caracteres.", 400)
            sets.append("clave = :clave")
            params["clave"] = generate_password_hash(password)

        if not sets:
            raise CustomException("No hay campos para actualizar.", 400)

        sets.append("updated_at = GETDATE()")
        self.querys.ia_usuarios_actualizar(id_usuario, sets, params)
        return self.tools.output(200, "Usuario actualizado correctamente.")

    def eliminar(self, data: dict):
        id_usuario = data.get("id")
        if not id_usuario:
            raise CustomException("El campo id es requerido.", 400)
        self.querys.ia_usuarios_eliminar(id_usuario)
        return self.tools.output(200, "Usuario eliminado correctamente.")
