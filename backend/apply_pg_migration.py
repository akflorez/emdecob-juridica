import os
import sys
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Asegurar que importamos los modelos correctamente
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def migrate():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
        
    print(f"Connecting to database...")
    result = urlparse(db_url)
    
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    conn.autocommit = True
    cursor = conn.cursor()

    def column_exists(table, column):
        cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name=%s AND column_name=%s
            """,
            (table, column)
        )
        return cursor.fetchone() is not None

    # Nuevos campos en case_publications (Fase 4 y Fase actual)
    new_columns = [
        # Fase 4
        ("estado_validacion", "VARCHAR(50) DEFAULT 'requiere_revision'"),
        ("match_score", "INTEGER DEFAULT 0"),
        ("texto_bloque_match", "TEXT"),
        ("motivo_descarte", "TEXT"),
        ("fuente_principal_validada", "BOOLEAN DEFAULT FALSE"),
        ("requiere_revision", "BOOLEAN DEFAULT TRUE"),
        ("elementos_detectados", "TEXT"),
        ("documento_nombre", "TEXT"),
        ("extraction_quality", "VARCHAR(50)"),
        ("validated_at", "TIMESTAMP"),
        # Fase Actual (Auditoría manual)
        ("validado_manual", "BOOLEAN DEFAULT FALSE"),
        ("aprobado_por_id", "INTEGER"),
        ("approved_at", "TIMESTAMP"),
        ("descartado_manual", "BOOLEAN DEFAULT FALSE"),
        ("descartado_por_id", "INTEGER"),
        ("discarded_at", "TIMESTAMP"),
        ("observacion_revision", "TEXT")
    ]

    for col_name, col_type in new_columns:
        if not column_exists("case_publications", col_name):
            print(f"Adding column {col_name} to case_publications...")
            cursor.execute(f"ALTER TABLE case_publications ADD COLUMN {col_name} {col_type}")

    # Tabla AuditLog
    print("Creating audit_logs table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            accion VARCHAR(100) NOT NULL,
            entidad VARCHAR(100),
            entidad_id INTEGER,
            ip VARCHAR(50),
            user_agent TEXT,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Índices para audit_logs
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_accion ON audit_logs(accion)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_entidad ON audit_logs(entidad)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_entidad_id ON audit_logs(entidad_id)")
    
    print("Migración legacy: Asegurando que publicaciones anteriores tengan estado_validacion...")
    cursor.execute("""
        UPDATE case_publications 
        SET estado_validacion = 'validado',
            motivo_match = 'Registro previo a validación estricta'
        WHERE (estado_validacion IS NULL OR estado_validacion = 'requiere_revision')
        AND match_score = 0 AND (texto_bloque_match IS NULL)
        AND created_at < NOW() - INTERVAL '1 day'
    """)
    print(f"Migrados {cursor.rowcount} registros legacy a 'validado'.")

    cursor.close()
    conn.close()
    print("Migración completada.")

if __name__ == "__main__":
    migrate()
