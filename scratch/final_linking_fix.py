
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Final task linking for Proyectos...")
        
        # 1. Global matching of tasks to lists based on names
        # We look for tasks where the title or description contains the name of a list
        conn.execute(text("""
            UPDATE tasks t
            SET list_id = l.id
            FROM project_lists l
            WHERE t.list_id IS NULL OR t.list_id NOT IN (SELECT id FROM project_lists)
            AND (t.title ILIKE '%' || l.name || '%' OR l.name ILIKE '%' || t.title || '%')
            AND LENGTH(l.name) > 5
        """))
        
        # 2. Specific fix for Alfredo Eduardo Cavadia Sanchez
        res_l = conn.execute(text("SELECT id FROM project_lists WHERE name ILIKE '%ALFREDO%EDUARDO%CAVADIA%'")).fetchone()
        if res_l:
            lid = res_l[0]
            conn.execute(text("UPDATE tasks SET list_id = :lid WHERE title ILIKE '%ALFREDO%EDUARDO%'"), {"lid": lid})
            print(f"Linked tasks to Alfredo's list (ID {lid})")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
