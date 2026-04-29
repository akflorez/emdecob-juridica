
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        case_id = 3054 # ID from previous search
        res = conn.execute(text("SELECT id, title FROM tasks WHERE case_id = :cid"), {"cid": case_id}).fetchall()
        print(f"Tasks for Case 3054 in emdecob_consultas: {len(res)}")
        for r in res:
            print(f"- {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
