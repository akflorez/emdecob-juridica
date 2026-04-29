
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT c.user_id, COUNT(t.id)
            FROM tasks t
            JOIN cases c ON t.case_id = c.id
            GROUP BY c.user_id
        """)).fetchall()
        print("Task Case User distribution in emdecob_consultas:")
        for r in res:
            print(f"- Case User ID: {r[0]} | Task Count: {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
