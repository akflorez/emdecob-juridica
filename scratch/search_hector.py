
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        name = "HECTOR WILLIAM PEREZ"
        # Search in demandado or demandante or alias
        res = conn.execute(text("""
            SELECT id, radicado, demandado, demandante, alias 
            FROM cases 
            WHERE demandado ILIKE :n OR demandante ILIKE :n OR alias ILIKE :n
        """), {"n": f"%{name}%"}).fetchall()
        print(f"Found {len(res)} matches:")
        for r in res:
            print(f"- ID: {r[0]} | Radicado: {r[1]} | Demandado: {r[2]} | Alias: {r[4]}")
            
except Exception as e:
    print(f"Error: {e}")
