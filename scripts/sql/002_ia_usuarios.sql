-- ============================================================
-- Tabla: dbo.ia_usuarios
-- Usuarios del sistema IA Cotizaciones con clave cifrada
-- NOTA: el campo 'clave' almacena el hash generado por
--       werkzeug.security.generate_password_hash (Python).
--       Debe ejecutarse DESPUES de 001_ia_roles.sql
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.tables
    WHERE name = 'ia_usuarios' AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
    CREATE TABLE dbo.ia_usuarios (
        id                    INT            NOT NULL IDENTITY(1,1),
        usuario               NVARCHAR(100)  NOT NULL,
        clave                 NVARCHAR(255)  NOT NULL,   -- hash werkzeug
        rol                   INT            NOT NULL,
        estado                TINYINT        NOT NULL CONSTRAINT DF_ia_usuarios_estado  DEFAULT 1,
        created_at            DATETIME2      NOT NULL CONSTRAINT DF_ia_usuarios_created DEFAULT GETDATE(),
        updated_at            DATETIME2      NOT NULL CONSTRAINT DF_ia_usuarios_updated DEFAULT GETDATE(),
        fecha_ultima_conexion DATETIME2      NULL,

        CONSTRAINT PK_ia_usuarios          PRIMARY KEY (id),
        CONSTRAINT UQ_ia_usuarios_usuario  UNIQUE      (usuario),
        CONSTRAINT FK_ia_usuarios_rol      FOREIGN KEY (rol) REFERENCES dbo.ia_roles(id)
    );

    PRINT 'Tabla dbo.ia_usuarios creada correctamente.';
END
ELSE
BEGIN
    PRINT 'Tabla dbo.ia_usuarios ya existe. No se realizo ninguna accion.';
END
GO

-- ── Verificar estructura ──────────────────────────────────
SELECT
    c.name          AS columna,
    t.name          AS tipo,
    c.max_length    AS longitud,
    c.is_nullable   AS permite_nulo
FROM sys.columns c
JOIN sys.types   t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('dbo.ia_usuarios')
ORDER BY c.column_id;
GO
