
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Checking due_dates of tasks...")
        res = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE due_date IS NOT NULL")).scalar()
        print(f"Tasks with due_date: {res}")
        
        if res > 0:
            sample = conn.execute(text("SELECT id, title, due_date FROM tasks WHERE due_date IS NOT NULL LIMIT 5")).fetchall()
            for s in sample:
                print(f"- Task {s[0]}: {s[1]} | Due: {s[2]}")
            
except Exception as e:
    print(f"Error: {e}")
