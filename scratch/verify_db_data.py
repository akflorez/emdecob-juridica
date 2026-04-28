import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@localhost:5432/juricob"

engine = create_engine(DATABASE_URL)

def check_counts():
    try:
        with engine.connect() as conn:
            # Get list of tables
            tables_res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in tables_res]
            print(f"Total tables found: {len(tables)}")

            for table in tables:
                try:
                    res = conn.execute(text(f"SELECT count(*) FROM {table}"))
                    count = res.scalar()
                    print(f"Table '{table}' count: {count}")
                except Exception as table_err:
                    print(f"Could not read table {table}: {table_err}")
                
            # If actuaciones table exists, check if any have content
            if 'actuaciones' in tables:
                res = conn.execute(text("SELECT count(*) FROM actuaciones WHERE description IS NOT NULL AND description != ''"))
                print(f"Actuaciones with description: {res.scalar()}")
                
            # If tasks table exists, check it
            if 'tasks' in tables:
                res = conn.execute(text("SELECT count(*) FROM tasks"))
                print(f"Tasks count: {res.scalar()}")

    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    check_counts()
