
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Fixing task links for CLARA INES MARTINEZ and others...")
        
        # 1. Find the List ID for Clara Ines Martinez
        res_l = conn.execute(text("SELECT id FROM project_lists WHERE name ILIKE '%CLARA%INES%MARTINEZ%'")).fetchone()
        if res_l:
            list_id = res_l[0]
            print(f"Found List ID for Clara Ines: {list_id}")
            
            # 2. Find any tasks that SHOULD be in this list (by title or current list_id)
            # Update tasks that have CLARA INES in title to this list_id
            res_t = conn.execute(text("UPDATE tasks SET list_id = :lid WHERE title ILIKE '%CLARA%INES%' AND (list_id IS NULL OR list_id != :lid)"), {"lid": list_id})
            print(f"Linked {res_t.rowcount} tasks to Clara Ines list.")
        else:
            print("Could not find list for Clara Ines Martinez")

        # 3. Global fix: Assign tasks to lists based on names if they are unlinked
        # This is a bit complex, but I'll do it for the most common ones
        conn.execute(text("""
            UPDATE tasks t
            SET list_id = l.id
            FROM project_lists l
            WHERE t.list_id IS NULL
            AND t.title ILIKE '%' || l.name || '%'
        """))
        
        # 4. Final check: Ensure tasks have a valid status (TO DO if null)
        conn.execute(text("UPDATE tasks SET status = 'TO DO' WHERE status IS NULL OR status = ''"))
        
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
