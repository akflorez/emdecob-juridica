
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Checking 'users' columns...")
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
        cols = [r[0] for r in res]
        print(f"Existing columns: {cols}")
        
        if 'email' not in cols:
            print("Adding 'email' column to 'users'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE"))
            conn.commit()
            print("Column added successfully")
        else:
            print("'email' column already exists")
            
        # Check 'tasks' table as well just in case
        print("\nChecking 'tasks' columns...")
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks'"))
        cols_tasks = [r[0] for r in res]
        print(f"Tasks columns: {cols_tasks}")
        
except Exception as e:
    print(f"Error: {e}")
