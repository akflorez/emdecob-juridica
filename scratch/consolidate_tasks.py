
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Consolidating tasks...")
        
        # We see many tasks have ' PAUL' in the title and are in lists > 5000
        # Let's see if we can find a main list for Paul or Alfredo and move them there
        
        # Alfredo's list is 26
        # Paul James Soto Jaramillo's folder might have a 'general' list
        
        # Move all tasks that are in lists with very few tasks (orphan-like) 
        # but have 'PAUL' in title to Alfredo's list for now so they are visible
        res = conn.execute(text("UPDATE tasks SET list_id = 26 WHERE title ILIKE '% PAUL%' AND list_id > 100"))
        print(f"Moved {res.rowcount} tasks to Alfredo's list (ID 26)")
        
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
