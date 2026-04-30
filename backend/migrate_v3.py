import sys
import os

# Añadir el directorio raíz al path para importar backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text

def get_db_url():
    # Intentar obtener la URL de la base de datos de forma robusta
    try:
        from backend.db import DATABASE_URL
        return DATABASE_URL
    except:
        return os.getenv("DATABASE_URL", "postgresql://emdecob:emdecob2026@db:5432/juricob")

def migrate():
    url = get_db_url()
    engine = create_engine(url)
    
    print(f"Conectando a {url} para migración de Datos Expertos...")
    
    with engine.connect() as conn:
        # 1. Tabla de etiquetas (tags)
        print("Verificando tabla 'tags'...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                color VARCHAR(50) DEFAULT '#3b82f6',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 2. Tabla de relación task_tags
        print("Verificando tabla 'task_tags'...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (task_id, tag_id)
            )
        """))

        # 3. Tabla task_attachments
        print("Verificando tabla 'task_attachments'...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS task_attachments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 4. Columna custom_fields en tasks
        print("Verificando columna 'custom_fields' en 'tasks'...")
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS custom_fields TEXT"))
        except Exception as e:
            print(f"Nota en custom_fields: {e}")

        # 5. Columna assignee_name en tasks
        print("Verificando columna 'assignee_name' en 'tasks'...")
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_name VARCHAR(200)"))
        except Exception as e:
            print(f"Nota en assignee_name: {e}")

        # 6. Tabla de relación task_assignees (Multiples responsables)
        print("Verificando tabla 'task_assignees'...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS task_assignees (
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                PRIMARY KEY (task_id, user_id)
            )
        """))

        conn.commit()
    
    print("✅ Migración Experta completada exitosamente.")

if __name__ == "__main__":
    migrate()
