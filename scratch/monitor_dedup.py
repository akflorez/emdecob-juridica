
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        f_count = conn.execute(text("SELECT COUNT(*) FROM folders")).scalar()
        l_count = conn.execute(text("SELECT COUNT(*) FROM project_lists")).scalar()
        print(f"Current state in juricob: {f_count} folders, {l_count} lists")
            
except Exception as e:
    print(f"Error: {e}")
