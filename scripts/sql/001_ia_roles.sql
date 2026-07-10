-- ============================================================
-- Tabla: dbo.ia_roles
-- Roles del sistema IA Cotizaciones
-- Ejecutar en DBeaver contra la BD configurada en .env
-- ============================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.tables
    WHERE name = 'ia_roles' AND schema_id = SCHEMA_ID('dbo')
)
BEGIN
    CREATE TABLE dbo.ia_roles (
        id     INT           NOT NULL IDENTITY(1,1),
        nombre NVARCHAR(100) NOT NULL,
        estado TINYINT       NOT NULL CONSTRAINT DF_ia_roles_estado DEFAULT 1,

        CONSTRAINT PK_ia_roles PRIMARY KEY (id)
    );

    PRINT 'Tabla dbo.ia_roles creada correctamente.';
END
ELSE
BEGIN
    PRINT 'Tabla dbo.ia_roles ya existe. No se realizo ninguna accion.';
END
GO

-- ── Seed de roles base ────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM dbo.ia_roles WHERE id = 1)
    INSERT INTO dbo.ia_roles (nombre, estado) VALUES (N'Administrador', 1);

IF NOT EXISTS (SELECT 1 FROM dbo.ia_roles WHERE id = 2)
    INSERT INTO dbo.ia_roles (nombre, estado) VALUES (N'Cotizador', 1);

PRINT 'Roles base insertados.';
GO

-- ── Verificar resultado ───────────────────────────────────
SELECT id, nombre, estado FROM dbo.ia_roles ORDER BY id;
GO
