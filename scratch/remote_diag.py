
import sqlalchemy
from sqlalchemy import create_engine, text

# Try remote postgres from check_remote_db.py
db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

print(f"Connecting to remote server: 84.247.130.122...")
try:
    engine = create_engine(db_url, connect_args={'connect_timeout': 10})
    with engine.connect() as conn:
        print("SUCCESSfully connected to REMOTE Postgres")
        res = conn.execute(text("SELECT COUNT(*) FROM cases"))
        print(f"Cases in Remote Postgres: {res.scalar()}")
        
        res = conn.execute(text("SELECT COUNT(*) FROM case_events"))
        print(f"Events in Remote Postgres: {res.scalar()}")
except Exception as e:
    print(f"Remote Postgres Error: {e}")
