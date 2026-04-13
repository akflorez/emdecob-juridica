import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB"),
    port=int(os.getenv("MYSQL_PORT", 3306))
)

def add_column_if_not_exists(cursor, table, column, definition):
    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
    if not cursor.fetchone():
        print(f"Adding column {column} to {table}...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

try:
    with conn.cursor() as cursor:
        # Table: cases
        add_column_if_not_exists(cursor, "cases", "alias", "VARCHAR(200)")
        add_column_if_not_exists(cursor, "cases", "last_hash", "VARCHAR(64)")
        add_column_if_not_exists(cursor, "cases", "current_hash", "VARCHAR(64)")
        add_column_if_not_exists(cursor, "cases", "last_check_at", "DATETIME")
        add_column_if_not_exists(cursor, "cases", "has_documents", "BOOLEAN DEFAULT FALSE")
        add_column_if_not_exists(cursor, "cases", "updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        
        # Table: case_events
        # Check if version exists
        add_column_if_not_exists(cursor, "case_events", "version", "INT DEFAULT 1")
        add_column_if_not_exists(cursor, "case_events", "is_current", "BOOLEAN DEFAULT TRUE")
        
        # Table: case_publications
        cursor.execute("SHOW TABLES LIKE 'case_publications'")
        if not cursor.fetchone():
            print("Creating case_publications table...")
            cursor.execute("""
                CREATE TABLE case_publications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    case_id INT NOT NULL,
                    fecha_publicacion DATE,
                    tipo_publicacion VARCHAR(255),
                    descripcion TEXT,
                    documento_url TEXT,
                    source_id VARCHAR(255) UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
                )
            """)

    conn.commit()
    print("Schema updated successfully!")
finally:
    conn.close()
