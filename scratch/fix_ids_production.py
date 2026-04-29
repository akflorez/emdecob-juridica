
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Starting ID correction in emdecob_consultas...")
        
        # 1. Update Case ownership (20 -> 2)
        res1 = conn.execute(text("UPDATE cases SET user_id = 2 WHERE user_id = 20"))
        print(f"Updated {res1.rowcount} cases (User 20 -> 2)")
        
        # 2. Update Task assignment (20 -> 2)
        res2 = conn.execute(text("UPDATE tasks SET assignee_id = 2 WHERE assignee_id = 20"))
        print(f"Updated {res2.rowcount} tasks (Assignee 20 -> 2)")
        
        # 3. Update Task creation (20 -> 2)
        res3 = conn.execute(text("UPDATE tasks SET creator_id = 2 WHERE creator_id = 20"))
        print(f"Updated {res3.rowcount} tasks (Creator 20 -> 2)")
        
        # 4. Check for any other tables that might have user_id
        # InvalidRadicado
        res4 = conn.execute(text("UPDATE invalid_radicados SET user_id = 2 WHERE user_id = 20"))
        print(f"Updated {res4.rowcount} invalid radicados (User 20 -> 2)")
        
        # Workspace ownership
        res5 = conn.execute(text("UPDATE workspaces SET owner_id = 2 WHERE owner_id = 20"))
        print(f"Updated {res5.rowcount} workspaces (Owner 20 -> 2)")
        
        # Workspace members
        res6 = conn.execute(text("UPDATE workspace_members SET user_id = 2 WHERE user_id = 20"))
        print(f"Updated {res6.rowcount} workspace memberships (User 20 -> 2)")

        conn.commit()
        print("Correction completed successfully.")
            
except Exception as e:
    print(f"Error: {e}")
