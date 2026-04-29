
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Force linking all orphaned tasks to Workspace 4...")
        
        # 1. Get a valid list_id from Workspace 4 to use as a bucket
        valid_list = conn.execute(text("""
            SELECT pl.id FROM project_lists pl
            JOIN folders f ON pl.folder_id = f.id
            WHERE f.workspace_id = 4
            LIMIT 1
        """)).fetchone()
        
        if valid_list:
            v_id = valid_list[0]
            print(f"Using List ID {v_id} as default bucket")
            
            # 2. Update all tasks that point to non-existent lists or lists in other workspaces
            # (Basically all tasks should now belong to Workspace 4's lists)
            conn.execute(text("""
                UPDATE tasks t
                SET list_id = :v_id
                WHERE t.list_id NOT IN (
                    SELECT pl.id FROM project_lists pl
                    JOIN folders f ON pl.folder_id = f.id
                    WHERE f.workspace_id = 4
                ) OR t.list_id IS NULL
            """), {"v_id": v_id})
            
            # 3. Final count
            count = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
            print(f"Total tasks in database: {count}")
            
            # 4. Check how many are in Alfredo's list (ID 26)
            alfredo_count = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE list_id = 26")).scalar()
            print(f"Tasks in Alfredo's list (ID 26): {alfredo_count}")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
