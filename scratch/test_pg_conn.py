import os
from sqlalchemy import create_engine, text

# DATABASE_URL = "postgresql://emdecob:emdecob2026@localhost:5432/juricob"
DATABASE_URL = "postgresql://emdecob:emdecob2026@127.0.0.1:5432/juricob"

print(f"Connecting to {DATABASE_URL}...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Successfully connected!")
        res = conn.execute(text("SELECT 1"))
        print(f"Result: {res.scalar()}")
        
        # Check tables
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in res]
        print(f"Tables: {tables}")
        
except Exception as e:
    print(f"Connection failed: {e}")
