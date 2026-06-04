import sqlalchemy
from sqlalchemy import create_engine, text

URL_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(URL_EMDECOB)
    with engine.connect() as conn:
        # Check parent task for case 1470
        print("=== CHECKING TASKS FOR CASE 1470 ===")
        # Wait, the radicado is 70001400300620180045500. Let's find the case first.
        case = conn.execute(text("SELECT id, radicado FROM cases WHERE radicado = '70001400300620180045500'")).fetchone()
        if not case:
            print("Case not found")
        else:
            cid = case[0]
            print(f"Case found: id={cid}")
            tasks = conn.execute(text("SELECT id, title, list_id, parent_id FROM tasks WHERE case_id = :cid"), {"cid": cid}).fetchall()
            print(f"Total tasks for case {cid}: {len(tasks)}")
            for t in tasks:
                print(f"  Task ID={t[0]} | Title={t[1]} | list_id={t[2]} | parent_id={t[3]}")
                
        # Check project lists
        print("\n=== CHECKING PROJECT LISTS ===")
        lists = conn.execute(text("SELECT id, name, folder_id FROM project_lists")).fetchall()
        print(f"Total project lists in DB: {len(lists)}")
        for l in lists[:10]:
            print(f"  List ID={l[0]} | Name={l[1]} | folder_id={l[2]}")
            
except Exception as e:
    print(f"Error: {e}")
