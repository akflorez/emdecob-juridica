
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT assignee_id, COUNT(*) FROM tasks GROUP BY assignee_id")).fetchall()
        print("Task assignees in emdecob_consultas:")
        for r in res:
            print(f"- ID: {r[0]} | Count: {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
