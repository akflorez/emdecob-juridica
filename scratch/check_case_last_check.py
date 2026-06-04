import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Checking last_check_at for Case 1470...")
        res = conn.execute(text("SELECT last_check_at, id_proceso, radicado FROM cases WHERE id = 1470"))
        row = res.fetchone()
        print(f"last_check_at: {row[0]} | id_proceso: {row[1]} | radicado: {row[2]}")
        
except Exception as e:
    print(f"Error: {e}")
