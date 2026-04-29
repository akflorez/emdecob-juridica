
import sqlalchemy
from sqlalchemy import create_engine, text
import re

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

def normalize(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', text).upper()

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Starting data re-linking in JURICOB...")
        
        # 1. Ensure all tasks have assignee_id = 2 if they were migrated (creator_id was 20 or 9997)
        res1 = conn.execute(text("UPDATE tasks SET assignee_id = 2 WHERE creator_id IN (2, 20, 9997) OR assignee_id IS NULL"))
        print(f"Updated {res1.rowcount} tasks assignees.")

        # 2. Re-link tasks to cases based on Radicado contained in title
        tasks = conn.execute(text("SELECT id, title, case_id FROM tasks WHERE title ~ '[0-9]{15,23}'")).fetchall()
        updated_tasks = 0
        for tid, title, current_case_id in tasks:
            # Extract possible radicado from title
            match = re.search(r'\d{15,23}', title)
            if match:
                rad = match.group(0)
                # Find matching case (even partial match at the end)
                case = conn.execute(text("SELECT id FROM cases WHERE radicado LIKE :r"), {"r": f"%{rad}"}).fetchone()
                if case and case[0] != current_case_id:
                    conn.execute(text("UPDATE tasks SET case_id = :cid WHERE id = :tid"), {"cid": case[0], "tid": tid})
                    updated_tasks += 1
        
        print(f"Re-linked {updated_tasks} tasks by radicado matching.")

        # 3. Special fix for HECTOR (from user screenshot)
        # Find HECTOR's case the user is viewing
        hector_case = conn.execute(text("SELECT id FROM cases WHERE demandado ILIKE '%HECTOR%WILLIAM%PEREZ%'")).fetchall()
        if len(hector_case) > 1:
            print(f"Found {len(hector_case)} HECTOR cases. Linking all HECTOR tasks to all of them (or the primary one).")
            primary_id = hector_case[0][0]
            # Link any task mentioning HECTOR to this case
            res_h = conn.execute(text("UPDATE tasks SET case_id = :cid WHERE title ILIKE '%HECTOR%WILLIAM%' OR title ILIKE '%CAVADIA%'"), {"cid": primary_id})
            print(f"Linked {res_h.rowcount} tasks for HECTOR/CAVADIA to Case ID {primary_id}")

        conn.commit()
        print("Data cleanup in JURICOB finished.")
            
except Exception as e:
    print(f"Error: {e}")
