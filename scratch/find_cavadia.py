
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Searching for CAVADIA...")
        res = conn.execute(text("SELECT id, name FROM project_lists WHERE name ILIKE '%CAVADIA%'")).fetchall()
        print(f"Results: {res}")
        
        if res:
            target_id = res[0][0]
            count = conn.execute(text("SELECT count(*) FROM tasks WHERE list_id = :tid"), {"tid": target_id}).scalar()
            print(f"Tasks for Cavadia (ID {target_id}): {count}")
            
            # If 0, try to find where the tasks are
            if count == 0:
                print("Searching for tasks with 'CAVADIA' in title...")
                task_samples = conn.execute(text("SELECT id, title, list_id FROM tasks WHERE title ILIKE '%CAVADIA%' LIMIT 5")).fetchall()
                print(f"Task samples: {task_samples}")

except Exception as e:
    print(f"Error: {e}")
