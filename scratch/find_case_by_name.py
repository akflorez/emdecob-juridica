
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        name = "HECTOR WILLIAM PEREZ"
        res = conn.execute(text("SELECT id, radicado, demandado FROM cases WHERE demandado LIKE :n"), {"n": f"%{name}%"}).fetchall()
        for r in res:
            print(f"ID: {r[0]} | Radicado: {repr(r[1])} | Demandado: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
