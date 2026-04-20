import os
from sqlalchemy import inspect, text
from backend.db import engine

def apply_migrations():
    print("Iniciando actualización de esquema robusta...")
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # Check columns for 'cases'
        cols_cases = [c['name'] for c in inspector.get_columns('cases')]
        if 'user_id' not in cols_cases:
            print("Agregando columna user_id a 'cases'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN user_id INTEGER;"))
            conn.execute(text("ALTER TABLE cases ADD CONSTRAINT fk_cases_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;"))
            conn.commit()
        else:
            print("La columna user_id ya existe en 'cases'.")

        # Check columns for 'invalid_radicados'
        cols_invalid = [c['name'] for c in inspector.get_columns('invalid_radicados')]
        if 'user_id' not in cols_invalid:
            print("Agregando columna user_id a 'invalid_radicados'...")
            conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN user_id INTEGER;"))
            conn.execute(text("ALTER TABLE invalid_radicados ADD CONSTRAINT fk_invalid_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;"))
            conn.commit()
        else:
            print("La columna user_id ya existe en 'invalid_radicados'.")
            
    print("Actualización de esquema finalizada.")

if __name__ == "__main__":
    apply_migrations()
