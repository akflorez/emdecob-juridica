
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Moving tasks to Alfredo's list...")
        
        # Target list ID for Alfredo
        lid = 26
        
        # Move tasks that have "ALFREDO" in title or description but are in other lists
        res = conn.execute(text("UPDATE tasks SET list_id = :lid WHERE (title ILIKE '%ALFREDO%' OR description ILIKE '%ALFREDO%') AND list_id != :lid"), {"lid": lid})
        print(f"Moved {res.rowcount} tasks to Alfredo's list")
        
        # Check if there are tasks for cases where the radicado starts with 11001... (common in your screenshots)
        # and move some to Alfredo if they are in general lists
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
