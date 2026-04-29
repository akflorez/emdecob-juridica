
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Listing columns for 'users'...")
        cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")).fetchall()
        print(f"Columns: {[c[0] for c in cols]}")

except Exception as e:
    print(f"Error: {e}")
