
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        # Search in demandado or radicado
        res = conn.execute(text("SELECT id, radicado, demandado FROM cases WHERE demandado ILIKE '%HECTOR WILLIAM PEREZ%'")).fetchall()
        print(f"Found {len(res)} matches in emdecob_consultas:")
        for r in res:
            print(f"- ID: {r[0]} | Radicado: {r[1]} | Demandado: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
