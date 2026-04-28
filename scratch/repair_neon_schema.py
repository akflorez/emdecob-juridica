
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
NEON_URL = os.getenv("NEON_URL")

def repair():
    if not NEON_URL:
        print("Missing NEON_URL")
        return
    
    engine = create_engine(NEON_URL)
    queries = [
        # Users
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        
        # Cases
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS user_id INTEGER;",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS alias VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS cedula VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS abogado VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS telefono VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS demandado VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS demandante VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS juzgado VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS id_proceso VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS last_hash VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS current_hash VARCHAR(255);",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS last_check_at TIMESTAMP;",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS fecha_radicacion DATE;",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ultima_actuacion DATE;",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS has_documents BOOLEAN DEFAULT FALSE;"
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
    repair()
