
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Assigning orphan tasks to User 2 in emdecob_consultas...")
        
        # Assign tasks to user 2 if they have no assignee
        res = conn.execute(text("UPDATE tasks SET assignee_id = 2 WHERE assignee_id IS NULL"))
        print(f"Assigned {res.rowcount} tasks to User 2")
        
        conn.commit()
        print("Assignment completed.")
            
except Exception as e:
    print(f"Error: {e}")
