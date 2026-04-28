
import os
from sqlalchemy import create_engine, text

CONTABO_PG = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

def repair_contabo():
    engine = create_engine(CONTABO_PG)
    queries = [
        # Workspaces
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(255);",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS visibility VARCHAR(255) DEFAULT 'TEAM_COLLABORATION';",
        
        # Folders
        "ALTER TABLE folders ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(255);",
        
        # Project Lists
        "ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(255);",
        "ALTER TABLE project_lists ADD COLUMN IF NOT EXISTS workspace_id INTEGER;",
        
        # Tasks
        "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS clickup_id VARCHAR(255);",
        "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_id INTEGER;",
        "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS case_id INTEGER;",
        "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS list_id INTEGER;",
        
        # Users
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;",
        
        # Cases
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS alias VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS id_proceso VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS user_id INTEGER;"
    ]
    
    with engine.connect() as conn:
        for q in queries:
            try:
                print(f"Running: {q}")
                conn.execute(text(q))
                conn.commit()
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    repair_contabo()
