
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT title FROM tasks LIMIT 100")).fetchall()
        print("First 100 task titles in juricob:")
        for r in res:
            print(f"- {r[0]}")
            
except Exception as e:
    print(f"Error: {e}")
