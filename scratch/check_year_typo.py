
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*) FROM cases WHERE radicado LIKE '%2026%'")).scalar()
        print(f"Radicados with 2026 in emdecob_consultas: {res}")
            
except Exception as e:
    print(f"Error: {e}")
