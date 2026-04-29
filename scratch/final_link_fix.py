
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Final task linking for Hector and Cavadia...")
        
        # Link Hector by Demandado Name
        sql_h = """
        UPDATE tasks t
        SET case_id = c.id
        FROM cases c
        WHERE c.demandado ILIKE '%HECTOR%WILLIAM%PEREZ%'
        AND (t.title ILIKE '%HECTOR%WILLIAM%' OR t.title ILIKE '%11001400303520260047100%')
        """
        res_h = conn.execute(text(sql_h))
        print(f"Linked {res_h.rowcount} tasks for Hector.")
        
        # Link Cavadia
        sql_c = """
        UPDATE tasks t
        SET case_id = c.id
        FROM cases c
        WHERE c.demandado ILIKE '%ALFREDO%EDUARDO%CAVADIA%'
        AND (t.title ILIKE '%ALFREDO%EDUARDO%' OR t.title ILIKE '%CAVADIA%')
        """
        res_c = conn.execute(text(sql_c))
        print(f"Linked {res_c.rowcount} tasks for Cavadia.")
        
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
