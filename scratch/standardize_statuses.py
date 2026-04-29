
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Standardizing statuses...")
        
        # Normalize statuses to lowercase 'to do', 'en progreso', etc.
        conn.execute(text("""
            UPDATE tasks 
            SET status = 'to do' 
            WHERE status IS NULL 
            OR LOWER(status) NOT IN ('to do', 'en progreso', 'revision', 'completado', 'in progress', 'complete')
        """))
        
        # Map 'in progress' to 'en progreso'
        conn.execute(text("UPDATE tasks SET status = 'en progreso' WHERE LOWER(status) = 'in progress'"))
        # Map 'complete' to 'completado'
        conn.execute(text("UPDATE tasks SET status = 'completado' WHERE LOWER(status) = 'complete'"))
        
        conn.commit()
        print("Statuses standardized successfully.")
            
except Exception as e:
    print(f"Error: {e}")
