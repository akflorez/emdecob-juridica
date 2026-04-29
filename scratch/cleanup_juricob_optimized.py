
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Starting optimized data re-linking in JURICOB...")
        
        # 1. Update all tasks to assignee_id = 2
        res1 = conn.execute(text("UPDATE tasks SET assignee_id = 2 WHERE assignee_id IS NULL OR assignee_id NOT IN (1, 2)"))
        print(f"Updated {res1.rowcount} task assignees.")

        # 2. Re-link tasks to cases where radicado is in the title
        # Optimized with a direct JOIN update
        # We look for a 23-digit radicado in the title and match it to cases
        # Note: Postgres substring/regex can be used
        sql = """
        UPDATE tasks t
        SET case_id = c.id
        FROM cases c
        WHERE t.case_id IS NULL 
        AND t.title ~ '[0-9]{23}'
        AND c.radicado = substring(t.title from '[0-9]{23}')
        """
        res2 = conn.execute(text(sql))
        print(f"Re-linked {res2.rowcount} tasks by exact 23-digit radicado matching.")

        # 3. Special fix for HECTOR (from user screenshot)
        # Demandado: HECTOR WILLIAM PEREZ
        # Link any task mentioning HECTOR to any case mentioning HECTOR
        sql_hector = """
        UPDATE tasks t
        SET case_id = (SELECT id FROM cases WHERE demandado ILIKE '%HECTOR%WILLIAM%PEREZ%' LIMIT 1)
        WHERE (t.title ILIKE '%HECTOR%WILLIAM%' OR t.title ILIKE '%CAVADIA%')
        AND (t.case_id IS NULL OR t.case_id NOT IN (SELECT id FROM cases WHERE demandado ILIKE '%HECTOR%WILLIAM%PEREZ%'))
        """
        res_h = conn.execute(text(sql_hector))
        print(f"Linked {res_h.rowcount} tasks for HECTOR/CAVADIA.")

        conn.commit()
        print("Optimized cleanup finished.")
            
except Exception as e:
    print(f"Error: {e}")
