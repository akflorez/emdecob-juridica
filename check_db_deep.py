import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_URL")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("--- SCHEMAS ---")
        res = conn.execute(text("SELECT schema_name FROM information_schema.schemata"))
        for row in res:
            print(row[0])
            
        print("\n--- TABLES (all) ---")
        res = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')"))
        for row in res:
            print(f"{row[0]}.{row[1]}")
            
        # Count cases in all found schemas
        print("\n--- CASE COUNTS ---")
        res = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'cases'"))
        for row in res:
            try:
                count_res = conn.execute(text(f"SELECT count(*) FROM {row[0]}.{row[1]}"))
                print(f"{row[0]}.{row[1]}: {count_res.scalar()}")
            except:
                pass
except Exception as e:
    print(f"Error: {e}")
