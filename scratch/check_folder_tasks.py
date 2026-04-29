
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        folder_name = "PAUL JAMES SOTO JARAMILLO"
        print(f"Checking lists and tasks for folder: {folder_name}")
        
        # Get folder ID
        folder_id = conn.execute(text("SELECT id FROM folders WHERE name = :n"), {"n": folder_name}).scalar()
        print(f"Folder ID: {folder_id}")
        
        if folder_id:
            lists = conn.execute(text("SELECT id, name FROM project_lists WHERE folder_id = :fid"), {"fid": folder_id}).fetchall()
            print(f"Found {len(lists)} lists.")
            for l in lists:
                t_count = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE list_id = :lid"), {"lid": l[0]}).scalar()
                if t_count > 0:
                    print(f"- List: {l[1]} (ID: {l[0]}) -> {t_count} tasks")
        
except Exception as e:
    print(f"Error: {e}")
