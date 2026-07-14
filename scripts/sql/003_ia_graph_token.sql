-- Tabla para cachear el token de Microsoft Graph API
-- Solo se guarda 1 token a la vez (se reemplaza cuando expira)

IF NOT EXISTS (
    SELECT * FROM sys.objects
    WHERE object_id = OBJECT_ID(N'dbo.ia_graph_token') AND type = N'U'
)
BEGIN
    CREATE TABLE dbo.ia_graph_token (
        id           INT IDENTITY(1,1) PRIMARY KEY,
        access_token NVARCHAR(MAX) NOT NULL,
        expires_at   DATETIME2     NOT NULL,
        created_at   DATETIME2     DEFAULT GETDATE()
    );
    PRINT 'Tabla dbo.ia_graph_token creada correctamente.';
END
ELSE
BEGIN
    PRINT 'La tabla dbo.ia_graph_token ya existe.';
END
