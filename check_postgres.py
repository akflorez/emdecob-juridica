import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

DATABASE_URL = "postgresql://emdecob:emdecob2026@localhost:5432/juricob"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT count(*) FROM cases"))
        count = res.scalar()
        print(f"Total cases in Local Postgres: {count}")
        
        # Check for recent records
        res = conn.execute(text("SELECT MAX(created_at) FROM cases"))
        max_date = res.scalar()
        print(f"Latest record date: {max_date}")
except Exception as e:
    print(f"Error connecting to local Postgres: {e}")
