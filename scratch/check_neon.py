import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_eWCA1gPd0ryo@ep-icy-thunder-akkkr42v.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require"

print(f"Connecting to Neon DB...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Successfully connected!")
        
        # Check tables
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in res]
        print(f"Tables: {tables}")
        
        for table in ['cases', 'case_events', 'tasks']:
            if table in tables:
                res = conn.execute(text(f"SELECT count(*) FROM {table}"))
                print(f"Table '{table}' count: {res.scalar()}")
            else:
                print(f"Table '{table}' NOT FOUND")
        
except Exception as e:
    print(f"Connection failed: {e}")
