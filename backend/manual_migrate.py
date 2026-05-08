from backend.main import engine
from sqlalchemy import text

def migrate():
    print("Iniciando migración manual...")
    with engine.connect() as conn:
        try:
            # Añadir user_name a task_comments
            conn.execute(text("ALTER TABLE task_comments ADD COLUMN IF NOT EXISTS user_name VARCHAR(255)"))
            print("Columna 'user_name' verificada/añadida en task_comments")
            
            # También verificamos columnas en 'tasks' por si acaso
            conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(100)"))
            conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_name VARCHAR(200)"))
            conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS custom_fields TEXT"))
            print("Columnas en 'tasks' verificadas/añadidas")
            
            conn.commit()
            print("Migración completada con éxito")
        except Exception as e:
            print(f"Error durante migración: {e}")

if __name__ == "__main__":
    migrate()
