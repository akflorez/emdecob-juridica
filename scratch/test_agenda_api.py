
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        user_id = 2
        print(f"Testing global tasks for user {user_id}:")
        # Global query for Agenda
        res = conn.execute(text("""
            SELECT t.id, t.title, t.due_date, t.assignee_id, c.user_id
            FROM tasks t
            LEFT OUTER JOIN cases c ON t.case_id = c.id
            WHERE (t.assignee_id = :uid OR c.user_id = :uid)
        """), {"uid": user_id}).fetchall()
        print(f"Total tasks found for Agenda: {len(res)}")
        if len(res) > 0:
            print("Sample task:", res[0])
            
except Exception as e:
    print(f"Error: {e}")
