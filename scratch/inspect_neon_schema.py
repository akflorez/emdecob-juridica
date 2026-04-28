
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
neon = os.getenv("NEON_URL")
engine = create_engine(neon)

tables = ['workspaces', 'folders', 'project_lists', 'tasks', 'users', 'cases']

for table in tables:
    print(f"\nTable: {table}")
    with engine.connect() as conn:
        try:
            r = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'"))
            for row in r:
                print(f"  - {row[0]} ({row[1]})")
        except Exception as e:
            print(f"  Error: {e}")
