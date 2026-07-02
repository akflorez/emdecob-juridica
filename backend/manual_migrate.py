import os
import sys

# Add parent directory to path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import engine
from sqlalchemy import text, inspect

def migrate():
    print("Iniciando migración manual...")
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        try:
            # Verificar y añadir columnas en 'users'
            cols_users = [c['name'] for c in inspector.get_columns('users')]
            if 'sync_with_clickup' not in cols_users:
                print("Añadiendo columna 'sync_with_clickup' a 'users'...")
                conn.execute(text("ALTER TABLE users ADD COLUMN sync_with_clickup BOOLEAN DEFAULT TRUE NOT NULL"))
            if 'clickup_api_token' not in cols_users:
                print("Añadiendo columna 'clickup_api_token' a 'users'...")
                conn.execute(text("ALTER TABLE users ADD COLUMN clickup_api_token VARCHAR(255)"))

            # Añadir user_name a task_comments
            cols_tc = [c['name'] for c in inspector.get_columns('task_comments')]
            if 'user_name' not in cols_tc:
                conn.execute(text("ALTER TABLE task_comments ADD COLUMN user_name VARCHAR(255)"))
                print("Columna 'user_name' verificada/añadida en task_comments")
            
            # También verificamos columnas en 'tasks' por si acaso
            cols_tasks = [c['name'] for c in inspector.get_columns('tasks')]
            if 'clickup_id' not in cols_tasks:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN clickup_id VARCHAR(100)"))
            if 'assignee_name' not in cols_tasks:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN assignee_name VARCHAR(200)"))
            if 'custom_fields' not in cols_tasks:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN custom_fields TEXT"))
            print("Columnas en 'tasks' verificadas/añadidas")
            
            conn.commit()
            print("Migración completada con éxito")
        except Exception as e:
            print(f"Error durante migración: {e}")

if __name__ == "__main__":
    migrate()
