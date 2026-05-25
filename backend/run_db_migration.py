import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to sys.path so that 'backend' package can be imported
project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(project_root)

from backend.db import DATABASE_URL

def main():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        print("Creating composite unique index on (case_id, source_id)...")
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_case_publication_case_source ON case_publications (case_id, source_id);") )
        
        print("Creating non-unique index on source_id for fast lookup...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_case_publications_source_id ON case_publications (source_id);") )
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    main()
