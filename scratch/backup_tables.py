import os
import json
from datetime import datetime, date
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
engine = create_engine(url)

# Custom JSON encoder to handle dates, datetimes, and other objects
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

backup_dir = "scratch/backup_db_before_restore"
os.makedirs(backup_dir, exist_ok=True)

tables = [
    "users",
    "companies",
    "cases",
    "case_events",
    "case_publications",
    "publicaciones_busquedas",
    "tasks",
    "search_jobs",
    "invalid_radicados",
    "audit_logs"
]

print(f"Starting backup of tables to: {backup_dir}")

with engine.connect() as conn:
    for table in tables:
        try:
            # Query all records
            res = conn.execute(text(f"SELECT * FROM {table};"))
            cols = res.keys()
            records = [dict(zip(cols, row)) for row in res]
            
            # Save to file
            file_path = os.path.join(backup_dir, f"{table}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(records, f, cls=CustomEncoder, indent=2, ensure_ascii=False)
                
            print(f"  Backup OK: {table} ({len(records)} rows) -> {file_path}")
        except Exception as e:
            print(f"  Backup FAILED: {table}. Error: {e}")

print("Backup process completed.")
