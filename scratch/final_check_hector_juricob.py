
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, radicado, demandado FROM cases WHERE demandado ILIKE '%HECTOR%WILLIAM%'")).fetchall()
        print("HECTOR cases in juricob:")
        for r in res:
            print(f"- ID: {r[0]} | Radicado: {r[1]} | Demandado: {r[2]}")
            t_count = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE case_id = :cid"), {"cid": r[0]}).scalar()
            print(f"  -> Tasks linked: {t_count}")
            
except Exception as e:
    print(f"Error: {e}")
