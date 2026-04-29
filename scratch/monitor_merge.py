
import sqlalchemy
from sqlalchemy import create_engine, text

DB_JURICOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(DB_JURICOB)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM cases")).scalar()
        print(f"Current cases in juricob: {count}")
            
except Exception as e:
    print(f"Error: {e}")
