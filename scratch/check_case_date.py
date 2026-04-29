
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT radicado, fecha_radicacion FROM cases WHERE id = 3054")).fetchone()
        print(f"Case 3054: Radicado={res[0]}, Fecha={res[1]}")
            
except Exception as e:
    print(f"Error: {e}")
