
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        list_name = "DEUDITH DEL SOCORRO OROZCO RIVERA"
        list_id = conn.execute(text("SELECT id FROM project_lists WHERE name = :n"), {"n": list_name}).scalar()
        print(f"List ID for '{list_name}': {list_id}")
        
        # Simulating backend logic for user 2
        user_id = 2
        query = text("""
            SELECT t.id, t.title 
            FROM tasks t
            LEFT OUTER JOIN cases c ON t.case_id = c.id
            WHERE t.list_id = :lid
            AND (t.assignee_id = :uid OR c.user_id = :uid)
        """)
        tasks = conn.execute(query, {"lid": list_id, "uid": user_id}).fetchall()
        print(f"Tasks found for user 2: {len(tasks)}")
        for t in tasks:
            print(f"- {t[1]}")
            
except Exception as e:
    print(f"Error: {e}")
