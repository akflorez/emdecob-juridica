
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT l.id, l.name, COUNT(t.id) as cnt
            FROM project_lists l
            JOIN tasks t ON t.list_id = l.id
            GROUP BY l.id, l.name
            ORDER BY cnt DESC
            LIMIT 10
        """)).fetchall()
        print("Lists with most tasks in JURICOB:")
        for r in res:
            print(f"- ID: {r[0]} | Name: {r[1]} | Tasks: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
