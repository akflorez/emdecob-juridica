
import sqlalchemy
from sqlalchemy import create_engine, text

DB_JURICOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(DB_JURICOB)
    with engine.connect() as conn:
        # Fix the sequence for cases
        max_id = conn.execute(text("SELECT MAX(id) FROM cases")).scalar() or 0
        conn.execute(text(f"SELECT setval('cases_id_seq', {max_id + 1})"))
        print(f"Reset cases_id_seq to {max_id + 1}")
        
        # Also fix tasks sequence just in case
        max_tid = conn.execute(text("SELECT MAX(id) FROM tasks")).scalar() or 0
        conn.execute(text(f"SELECT setval('tasks_id_seq', {max_tid + 1})"))
        print(f"Reset tasks_id_seq to {max_tid + 1}")
        
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
