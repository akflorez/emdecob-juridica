
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, radicado FROM cases WHERE radicado LIKE '%47100%'")).fetchall()
        print(f"Matches in emdecob_consultas:")
        for r in res:
            print(f"- ID: {r[0]} | Radicado: {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
