import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def migrate():
    print(f"Migrating database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    def column_exists(table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns

    # Nuevos campos de trazabilidad en case_publications
    new_columns = [
        ("validado_manual", "BOOLEAN DEFAULT 0"),
        ("aprobado_por_id", "INTEGER"),
        ("approved_at", "DATETIME"),
        ("descartado_manual", "BOOLEAN DEFAULT 0"),
        ("descartado_por_id", "INTEGER"),
        ("discarded_at", "DATETIME"),
        ("observacion_revision", "TEXT")
    ]

    for col_name, col_type in new_columns:
        if not column_exists("case_publications", col_name):
            print(f"Adding column {col_name} to case_publications...")
            cursor.execute(f"ALTER TABLE case_publications ADD COLUMN {col_name} {col_type}")

    # Tabla AuditLog
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            accion VARCHAR(100) NOT NULL,
            entidad VARCHAR(100),
            entidad_id INTEGER,
            ip VARCHAR(50),
            user_agent TEXT,
            metadata_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    # Índices para audit_logs
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_accion ON audit_logs(accion)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_entidad ON audit_logs(entidad)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_entidad_id ON audit_logs(entidad_id)")
    
    print("Migración legacy: Asegurando que publicaciones anteriores tengan estado_validacion...")
    # Migrar legacy: Si un documento ya existía y no tiene estado_validacion ni score
    # Lo pasamos a 'validado' pero indicamos que fue legacy.
    cursor.execute("""
        UPDATE case_publications 
        SET estado_validacion = 'validado',
            motivo_match = 'Registro previo a validación estricta'
        WHERE estado_validacion IS NULL OR estado_validacion = 'requiere_revision'
        AND match_score = 0 AND (texto_bloque_match IS NULL)
        AND id IN (
            SELECT id FROM case_publications 
            WHERE created_at < datetime('now', '-1 day')
        )
    """)
    print(f"Migrados {cursor.rowcount} registros legacy a 'validado'.")

    conn.commit()
    conn.close()
    print("Migración completada.")

if __name__ == "__main__":
    migrate()
