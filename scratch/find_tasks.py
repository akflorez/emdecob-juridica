
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Finding tasks distribution...")
        res = conn.execute(text("""
            SELECT l.name, f.name, COUNT(t.id) 
            FROM tasks t
            JOIN project_lists l ON t.list_id = l.id
            JOIN folders f ON l.folder_id = f.id
            GROUP BY l.name, f.name
            ORDER BY COUNT(t.id) DESC
            LIMIT 20
        """)).fetchall()
        for r in res:
            print(f"- Folder: {r[1]} | List: {r[0]} | Tasks: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
