
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Deep task linking for Alfredo...")
        
        # Find Alfredo's Case IDs
        cases = conn.execute(text("SELECT id, radicado FROM cases WHERE abogado ILIKE '%ALFREDO%CAVADIA%'")).fetchall()
        case_ids = [c[0] for c in cases]
        radicados = [c[1] for c in cases if c[1]]
        
        print(f"Found {len(case_ids)} cases for Alfredo")
        
        # Find Alfredo's List ID
        res_l = conn.execute(text("SELECT id FROM project_lists WHERE name ILIKE '%ALFREDO%CAVADIA%'")).fetchone()
        if res_l and case_ids:
            lid = res_l[0]
            
            # Update tasks that are linked to those cases
            res = conn.execute(text("UPDATE tasks SET list_id = :lid WHERE case_id IN :cids"), {"lid": lid, "cids": tuple(case_ids)})
            print(f"Linked {res.rowcount} tasks via case_id")
            
            # Update tasks that mention those radicados in title/desc
            for rad in radicados:
                if len(rad) > 10:
                    conn.execute(text("UPDATE tasks SET list_id = :lid WHERE (title ILIKE :r OR description ILIKE :r) AND list_id IS NULL"), {"lid": lid, "r": f"%{rad}%"})
            
            # Final check
            count = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE list_id = :lid"), {"lid": lid}).scalar()
            print(f"Total tasks now in Alfredo's list: {count}")
            
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
