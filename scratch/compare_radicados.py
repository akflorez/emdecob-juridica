
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, radicado FROM cases WHERE radicado = '11001400303520200047100'")).fetchone()
        print(f"Exact match 2020: {res}")
        
        res2 = conn.execute(text("SELECT id, radicado FROM cases WHERE radicado = '11001400303520260047100'")).fetchone()
        print(f"Exact match 2026: {res2}")
            
except Exception as e:
    print(f"Error: {e}")
