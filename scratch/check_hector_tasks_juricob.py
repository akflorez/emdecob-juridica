
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, title FROM tasks WHERE case_id = 1932")).fetchall()
        print(f"Tasks for HECTOR (ID 1932) in JURICOB: {len(res)}")
        for r in res:
            print(f"- {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
