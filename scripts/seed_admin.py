"""
Script para crear el primer usuario administrador en dbo.ia_usuarios.
Ejecutar UNA sola vez desde la carpeta backend/:

    python scripts/seed_admin.py

Requiere que las tablas ia_roles e ia_usuarios ya existan (ejecutar
primero los scripts SQL 001 y 002).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from sqlalchemy import text
from Config.db import session_maker


def crear_usuario():
    usuario = input("Usuario DMS      : ").strip()
    if not usuario:
        print("ERROR: El usuario no puede estar vacío.")
        return

    clave = input("Contraseña       : ").strip()
    if len(clave) < 6:
        print("ERROR: La contraseña debe tener al menos 6 caracteres.")
        return

    print("\nRoles disponibles:")
    print("  1 → Administrador")
    print("  2 → Cotizador")
    rol = input("Rol (1/2)        : ").strip()
    if rol not in ("1", "2"):
        print("ERROR: Rol inválido. Ingresa 1 o 2.")
        return

    clave_hash = generate_password_hash(clave)

    db = session_maker()
    try:
        # Verificar si el usuario ya existe
        existe = db.execute(
            text("SELECT COUNT(*) FROM dbo.ia_usuarios WHERE usuario = :u"),
            {"u": usuario}
        ).scalar()

        if existe:
            print(f"\nERROR: El usuario '{usuario}' ya existe en dbo.ia_usuarios.")
            return

        db.execute(
            text("""
                INSERT INTO dbo.ia_usuarios (usuario, clave, rol, estado)
                VALUES (:usuario, :clave, :rol, 1)
            """),
            {"usuario": usuario, "clave": clave_hash, "rol": int(rol)}
        )
        db.commit()
        print(f"\nUsuario '{usuario}' creado correctamente con rol {rol}.")

    except Exception as e:
        db.rollback()
        print(f"\nERROR al insertar: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    crear_usuario()
