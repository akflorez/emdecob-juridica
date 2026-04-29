
import sqlalchemy
from sqlalchemy import create_engine, text
import os

# Try local postgres
db_url = "postgresql://emdecob:emdecob2026@127.0.0.1:5432/juricob"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Successfully connected to local Postgres")
        res = conn.execute(text("SELECT COUNT(*) FROM cases"))
        print(f"Cases in Postgres: {res.scalar()}")
except Exception as e:
    print(f"Postgres Error: {e}")

# Try connecting to postgres db first to list others
try:
    engine = create_engine("postgresql://emdecob:emdecob2026@127.0.0.1:5432/postgres")
    with engine.connect() as conn:
        print("Connected to 'postgres' db")
        res = conn.execute(text("SELECT datname FROM pg_database"))
        print(f"Databases: {[r[0] for r in res]}")
except Exception as e:
    print(f"Postgres list error: {e}")
