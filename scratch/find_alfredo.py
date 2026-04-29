
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Searching for any list with 'ALFREDO' and its tasks:")
        res = conn.execute(text("""
            SELECT l.id, l.name, f.name, COUNT(t.id)
            FROM project_lists l
            JOIN folders f ON l.folder_id = f.id
            LEFT JOIN tasks t ON t.list_id = l.id
            WHERE l.name ILIKE '%ALFREDO%'
            GROUP BY l.id, l.name, f.name
        """)).fetchall()
        for r in res:
            print(f"- ID: {r[0]} | List: {r[1]} | Folder: {r[2]} | Tasks: {r[3]}")
            
except Exception as e:
    print(f"Error: {e}")
