
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        radicado = "11001418909420260125200"
        res = conn.execute(text("SELECT user_id FROM cases WHERE radicado = :r"), {"r": radicado}).scalar()
        print(f"Case user_id: {res}")
except Exception as e:
    print(f"Error: {e}")
