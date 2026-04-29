
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        radicado = "11001418909420260125200"
        print(f"Checking tasks for radicado: {radicado}")
        
        # Get case ID
        case_id = conn.execute(text("SELECT id FROM cases WHERE radicado = :r"), {"r": radicado}).scalar()
        print(f"Case ID: {case_id}")
        
        if case_id:
            tasks = conn.execute(text("SELECT id, title, assignee_id FROM tasks WHERE case_id = :cid"), {"cid": case_id}).fetchall()
            print(f"Found {len(tasks)} tasks:")
            for t in tasks:
                print(f"- ID: {t[0]}, Title: {t[1]}, Assignee: {t[2]}")
                
        # Check current user 'jurico_emdecob'
        user_id = conn.execute(text("SELECT id FROM users WHERE username = 'jurico_emdecob'")).scalar()
        print(f"\nCurrent user (jurico_emdecob) ID: {user_id}")
        
except Exception as e:
    print(f"Error: {e}")
