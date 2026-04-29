
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        case_id = 3054
        res = conn.execute(text("SELECT COUNT(*) FROM case_events WHERE case_id = :cid"), {"cid": case_id}).scalar()
        print(f"Events for Case 3054 in emdecob_consultas: {res}")
            
except Exception as e:
    print(f"Error: {e}")
