
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT f.id, f.name, COUNT(t.id) 
            FROM folders f
            JOIN project_lists l ON l.folder_id = f.id
            JOIN tasks t ON t.list_id = l.id
            GROUP BY f.id, f.name
            HAVING COUNT(t.id) > 0
        """)).fetchall()
        print("Populated folders in juricob:")
        for r in res:
            print(f"- ID: {r[0]} | Name: {r[1]} | Tasks: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
