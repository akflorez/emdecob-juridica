
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        list_name = "ALFREDO EDUARDO CAVADIA SANCHEZ"
        print(f"Checking tasks for list: {list_name}")
        
        # Get list ID
        list_id = conn.execute(text("SELECT id FROM project_lists WHERE name = :n"), {"n": list_name}).scalar()
        print(f"List ID: {list_id}")
        
        if list_id:
            tasks = conn.execute(text("SELECT id, title, assignee_id, case_id FROM tasks WHERE list_id = :lid"), {"lid": list_id}).fetchall()
            print(f"Found {len(tasks)} tasks:")
            for t in tasks:
                print(f"- ID: {t[0]}, Title: {t[1]}, Assignee: {t[2]}, Case: {t[3]}")
                if t[3]:
                    c_user = conn.execute(text("SELECT user_id FROM cases WHERE id = :cid"), {"cid": t[3]}).scalar()
                    print(f"  Case User ID: {c_user}")
        
except Exception as e:
    print(f"Error: {e}")
