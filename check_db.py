import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_URL")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    res = conn.execute(text("SELECT count(*) FROM cases"))
    count = res.scalar()
    print(f"Total cases: {count}")
    
    res = conn.execute(text("SELECT count(*) FROM case_publications"))
    pub_count = res.scalar()
    print(f"Total publications: {pub_count}")
