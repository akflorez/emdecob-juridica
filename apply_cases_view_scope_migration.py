import os
from sqlalchemy import inspect, text
from backend.db import engine

def apply_migrations():
    print("Iniciando migración de campo cases_view_scope...")
    inspector = inspect(engine)
    
    # Run on default engine first
    with engine.connect() as conn:
        cols_users = [c['name'] for c in inspector.get_columns('users')]
        if 'cases_view_scope' not in cols_users:
            print("Agregando columna cases_view_scope a 'users'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN cases_view_scope VARCHAR(50) DEFAULT 'ALL';"))
            conn.commit()
            print("Columna cases_view_scope agregada con éxito.")
        else:
            print("La columna cases_view_scope ya existe en 'users'.")

    # To be extremely safe, run on both databases if we have direct access to remote host
    from sqlalchemy import create_engine
    for db_name in ["juricob", "emdecob_consultas"]:
        url = f"postgresql://emdecob:emdecob2026@84.247.130.122:5432/{db_name}"
        try:
            temp_engine = create_engine(url)
            with temp_engine.connect() as conn:
                temp_inspector = inspect(temp_engine)
                cols = [c['name'] for c in temp_inspector.get_columns('users')]
                if 'cases_view_scope' not in cols:
                    print(f"Agregando cases_view_scope a {db_name}...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN cases_view_scope VARCHAR(50) DEFAULT 'ALL';"))
                    conn.commit()
                else:
                    print(f"cases_view_scope ya existe en {db_name}.")
        except Exception as e:
            print(f"Error migrando {db_name} directamente: {e}")

if __name__ == "__main__":
    apply_migrations()
