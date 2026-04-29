
import sqlalchemy
from sqlalchemy import create_engine, text
import re

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

def extract_radicado(text_str):
    if not text_str: return None
    # Look for 23 digit radicado
    match = re.search(r'\d{23}', text_str)
    if match: return match.group(0)
    return None

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Starting massive task-to-case linking...")
        
        # 1. Get all tasks that have no case_id
        tasks = conn.execute(text("SELECT id, title, description FROM tasks WHERE case_id IS NULL")).fetchall()
        print(f"Analyzing {len(tasks)} tasks...")
        
        linked_count = 0
        for tid, title, desc in tasks:
            rad = extract_radicado(title) or extract_radicado(desc)
            if rad:
                # Find the case
                case = conn.execute(text("SELECT id FROM cases WHERE radicado = :r"), {"r": rad}).fetchone()
                if case:
                    conn.execute(text("UPDATE tasks SET case_id = :cid WHERE id = :tid"), {"cid": case[0], "tid": tid})
                    linked_count += 1
        
        print(f"Successfully linked {linked_count} tasks to their judicial processes.")
        
        # 2. Fix Ana Valentina Ruiz Cardona (ID 1726 or similar)
        # Search for her list
        res_l = conn.execute(text("SELECT id FROM project_lists WHERE name ILIKE '%ANA%VALENTINA%RUIZ%'")).fetchone()
        if res_l:
            lid = res_l[0]
            # Link tasks mentioning her
            res = conn.execute(text("UPDATE tasks SET list_id = :lid WHERE (title ILIKE '%ANA%VALENTINA%' OR description ILIKE '%ANA%VALENTINA%') AND list_id != :lid"), {"lid": lid})
            print(f"Moved {res.rowcount} tasks to Ana Valentina's list (ID {lid})")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
