import os
import sys
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def migrate():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
        
    print(f"Connecting to database for SaaS migration...")
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

    # 1. Crear tabla companies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            nit VARCHAR(50),
            estado VARCHAR(50) DEFAULT 'activo',
            limite_usuarios INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Insertar empresa default si no existe
    cursor.execute("SELECT id FROM companies WHERE nombre = 'Empresa Default'")
    empresa_default = cursor.fetchone()
    if not empresa_default:
        cursor.execute("INSERT INTO companies (nombre) VALUES ('Empresa Default') RETURNING id")
        empresa_default_id = cursor.fetchone()[0]
        print(f"Empresa Default creada con ID {empresa_default_id}")
    else:
        empresa_default_id = empresa_default[0]
        print(f"Empresa Default ya existe con ID {empresa_default_id}")

    # 3. Crear tablas de roles y permisos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            description VARCHAR(255)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
            PRIMARY KEY (role_id, permission_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, role_id)
        )
    """)

    # 4. Modificar tablas existentes agregando company_id
    def add_company_column(table_name):
        # Verifica si existe
        cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name='company_id'",
            (table_name,)
        )
        if not cursor.fetchone():
            print(f"Adding company_id to {table_name}...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE")
            # Asignar a empresa default
            cursor.execute(f"UPDATE {table_name} SET company_id = %s", (empresa_default_id,))

    tables_to_update = ["users", "cases", "publicaciones_busquedas", "audit_logs"]
    for table in tables_to_update:
        add_company_column(table)

    cursor.close()
    conn.close()
    print("Migración SaaS completada.")

if __name__ == "__main__":
    migrate()
