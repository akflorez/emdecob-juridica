import os
import sys
from sqlalchemy import create_engine, text

sys.path.append(os.getcwd())
from backend.db import DATABASE_URL

def main():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.begin() as conn:
        print("Checking if unique index ix_case_publications_source_id exists...")
        # Check if the index is unique in PostgreSQL
        # We can run an ALTER or DROP statement directly.
        # In PostgreSQL, we can drop the index directly:
        print("Dropping index ix_case_publications_source_id if it exists...")
        conn.execute(text("DROP INDEX IF EXISTS ix_case_publications_source_id;"))
        
        print("Creating non-unique index ix_case_publications_source_id on source_id...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_case_publications_source_id ON case_publications (source_id);"))
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    main()
