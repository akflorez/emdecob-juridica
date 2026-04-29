
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE case_id IS NOT NULL")).scalar()
        print(f"Tasks with case_id: {count}")
        
        if count > 0:
            res = conn.execute(text("SELECT id, title, case_id FROM tasks WHERE case_id IS NOT NULL LIMIT 5")).fetchall()
            for r in res:
                print(f"Task ID: {r[0]} | Title: {r[1]} | Case ID: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
