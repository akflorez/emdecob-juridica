
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Checking columns in 'tasks'...")
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks'"))
        cols = [r[0] for r in res]
        print(f"Columns: {cols}")
        
        # Check for data
        count = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
        print(f"Total tasks: {count}")
except Exception as e:
    print(f"Error: {e}")
