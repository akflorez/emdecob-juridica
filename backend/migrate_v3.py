import sys
import os

# Añadir el directorio raíz al path para importar backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from backend.database import DATABASE_URL
from backend.models import Base

def migrate():
    engine = create_engine(DATABASE_URL)
    
    print(f"Conectando a la base de datos para migración v3...")
    
    with engine.connect() as conn:
        # 1. Crear tabla task_attachments si no existe
        print("Verificando tabla task_attachments...")
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
        
        # 2. Añadir columna custom_fields a tasks si no existe
        print("Verificando columna custom_fields en tabla tasks...")
        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN custom_fields TEXT"))
            print("Columna custom_fields añadida exitosamente.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("La columna custom_fields ya existe.")
            else:
                print(f"Nota: {e}")

        conn.commit()
    
    print("Migración v3 completada exitosamente.")

if __name__ == "__main__":
    migrate()
