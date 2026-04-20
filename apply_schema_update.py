import os
from sqlalchemy import text
from backend.db import engine

def apply_migrations():
    print("Iniciando actualización de esquema...")
    
    queries = [
        # Para Case
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
        "CREATE INDEX IF NOT EXISTS idx_cases_user_id ON cases(user_id);",
        
        # Para InvalidRadicado
        "ALTER TABLE invalid_radicados ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
        "CREATE INDEX IF NOT EXISTS idx_invalid_radicados_user_id ON invalid_radicados(user_id);",
    ]
    
    with engine.connect() as conn:
        for query in queries:
            try:
                # Nota: IF NOT EXISTS funciona bien en Postgres. 
                # En MySQL 8.0+ se puede usar pero para columnas es más complejo.
                # Intentaremos ejecutarlo y capturar errores si ya existe.
                print(f"Ejecutando: {query}")
                conn.execute(text(query))
                conn.commit()
            except Exception as e:
                print(f"Nota/Error: {e}")
    
    print("Actualización de esquema finalizada.")

if __name__ == "__main__":
    apply_migrations()
