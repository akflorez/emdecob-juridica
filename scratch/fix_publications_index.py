import os
from sqlalchemy import create_engine, text

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

def run_migration():
    print(f"Connecting to database at {db_url}...")
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Drop the unique index ix_case_publications_source_id if it exists
            print("Dropping unique index ix_case_publications_source_id...")
            conn.execute(text("DROP INDEX IF EXISTS ix_case_publications_source_id;"))
            
            # Create ix_case_publications_source_id as a regular index
            print("Creating non-unique index ix_case_publications_source_id...")
            conn.execute(text("CREATE INDEX ix_case_publications_source_id ON case_publications (source_id);"))
            
            # Drop constraint/index uq_case_publication_case_source if it exists
            print("Dropping constraint uq_case_publication_case_source if exists...")
            conn.execute(text("ALTER TABLE case_publications DROP CONSTRAINT IF EXISTS uq_case_publication_case_source;"))
            conn.execute(text("DROP INDEX IF EXISTS uq_case_publication_case_source;"))
            
            # Create uq_case_publication_case_source unique index on (case_id, source_id)
            print("Creating unique index uq_case_publication_case_source...")
            conn.execute(text("CREATE UNIQUE INDEX uq_case_publication_case_source ON case_publications (case_id, source_id);"))
            
            trans.commit()
            print("Migration completed successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Error executing migration: {e}")
            raise

if __name__ == "__main__":
    run_migration()
