import os
from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://emdecob:Emdecob2026*@127.0.0.1:3306/emdecob_consultas"

print(f"Connecting to MySQL...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Successfully connected!")
        
        # Check tables
        res = conn.execute(text("SHOW TABLES"))
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
