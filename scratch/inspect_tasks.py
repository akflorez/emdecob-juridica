
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        list_id = 37
        print(f"Inspecting tasks for list_id {list_id}")
        res = conn.execute(text("SELECT id, title, assignee_id, case_id FROM tasks WHERE list_id = :lid"), {"lid": list_id}).fetchall()
        for r in res:
            print(f"- Task ID: {r[0]} | Title: {r[1]} | Assignee: {r[2]} | Case: {r[3]}")
            if r[3]:
                c_user = conn.execute(text("SELECT user_id FROM cases WHERE id = :cid"), {"cid": r[3]}).scalar()
                print(f"  Case User ID: {c_user}")
                
except Exception as e:
    print(f"Error: {e}")
