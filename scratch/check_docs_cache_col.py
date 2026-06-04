import sqlalchemy
from sqlalchemy import create_engine, text

URL_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(URL_EMDECOB)
    with engine.connect() as conn:
        # Check columns of case_events
        cols = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'case_events'")).fetchall()
        print("Columns in case_events:")
        for c in cols:
            print(f"  {c[0]} ({c[1]})")
except Exception as e:
    print(f"Error: {e}")
