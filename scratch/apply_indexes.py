import sqlalchemy
from sqlalchemy import create_engine, text

URL_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

def apply_indexes():
    print("Connecting to database to apply indexes...")
    engine = create_engine(URL_EMDECOB)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Creating index on tasks(list_id)...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_list_id ON tasks(list_id)"))
            
            print("Creating index on tasks(parent_id)...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)"))
            
            print("Creating index on tasks(assignee_id)...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_assignee_id ON tasks(assignee_id)"))
            
            trans.commit()
            print("All indexes created successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Error applying indexes: {e}")

if __name__ == "__main__":
    apply_indexes()
