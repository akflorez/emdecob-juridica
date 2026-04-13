import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 10})

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT count(*) FROM cases"))
        count = res.scalar()
        print(f"SUCCESS! Total cases in Rremote Postgres: {count}")
except Exception as e:
    print(f"Error connecting to production Postgres: {e}")
