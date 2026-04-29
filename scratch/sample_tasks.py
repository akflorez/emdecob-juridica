
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Total tasks in DB:", conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar())
        
        print("\nSampling 10 tasks with their hierarchy:")
        res = conn.execute(text("""
            SELECT t.id, t.title, t.list_id, l.name, f.name, t.assignee_id
            FROM tasks t
            LEFT JOIN project_lists l ON t.list_id = l.id
            LEFT JOIN folders f ON l.folder_id = f.id
            LIMIT 10
        """)).fetchall()
        for r in res:
            print(f"- Task {r[0]}: {r[1]} | List: {r[3]} (ID: {r[2]}) | Folder: {r[4]} | Assignee: {r[5]}")
            
except Exception as e:
    print(f"Error: {e}")
