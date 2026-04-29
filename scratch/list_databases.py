
import sqlalchemy
from sqlalchemy import create_engine, text

# Connect to 'postgres' database to list other databases
SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/postgres"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false")).fetchall()
        print("Databases on server:")
        for r in res:
            print(f"- {r[0]}")
            
except Exception as e:
    print(f"Error: {e}")
