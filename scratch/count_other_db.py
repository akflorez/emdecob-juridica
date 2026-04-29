
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM cases")).scalar()
        print(f"Total cases in emdecob_consultas: {count}")
        
        t_count = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
        print(f"Total tasks in emdecob_consultas: {t_count}")
            
except Exception as e:
    print(f"Error: {e}")
