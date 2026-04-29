
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, title, assignee_id FROM tasks WHERE list_id = 5829")).fetchall()
        print(f"Tasks in List 5829 (HECTOR):")
        for r in res:
            print(f"- ID: {r[0]} | Title: {r[1]} | Assignee: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
