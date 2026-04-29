
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, radicado FROM cases WHERE id = 2518")).fetchone()
        print(f"Case 2518: {res}")
            
except Exception as e:
    print(f"Error: {e}")
