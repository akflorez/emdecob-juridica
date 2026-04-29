
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Use 127.0.0.1 as in db.py
DATABASE_URL = "postgresql://emdecob:emdecob2026@127.0.0.1:5432/juricob"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connected successfully to Postgres")
        
        cases = conn.execute(text("SELECT COUNT(*) FROM cases")).scalar()
        events = conn.execute(text("SELECT COUNT(*) FROM case_events")).scalar()
        tasks = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
        
        print(f"Cases: {cases}")
        print(f"Events: {events}")
        print(f"Tasks: {tasks}")
        
        if cases > 0:
            print("\nSample Cases:")
            res = conn.execute(text("SELECT radicado, demandado FROM cases LIMIT 5"))
            for row in res:
                print(f"- {row[0]}: {row[1]}")
                
except Exception as e:
    print(f"Error: {e}")
