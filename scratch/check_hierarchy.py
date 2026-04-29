
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        ws_count = conn.execute(text("SELECT COUNT(*) FROM workspaces")).scalar()
        folder_count = conn.execute(text("SELECT COUNT(*) FROM folders")).scalar()
        list_count = conn.execute(text("SELECT COUNT(*) FROM project_lists")).scalar()
        task_count = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
        
        print(f"Workspaces: {ws_count}")
        print(f"Folders: {folder_count}")
        print(f"Lists: {list_count}")
        print(f"Tasks: {task_count}")
        
        if ws_count == 0:
            print("WARNING: No workspaces found. The hierarchy is missing!")
except Exception as e:
    print(f"Error: {e}")
