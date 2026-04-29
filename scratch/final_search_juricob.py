
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, radicado FROM cases WHERE radicado ILIKE '%47100%'")).fetchall()
        print(f"Juricob matches: {res}")
        
        res2 = conn.execute(text("SELECT id, radicado FROM cases WHERE demandado ILIKE '%HECTOR%'")).fetchall()
        print(f"Juricob hector matches: {res2}")
            
except Exception as e:
    print(f"Error: {e}")
