
import sqlalchemy
from sqlalchemy import create_engine, text

NEON_URL = "postgresql://neondb_owner:npg_eWCA1gPd0ryo@ep-icy-thunder-akkkr42v.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require"

print("Connecting to Neon...")
try:
    engine = create_engine(NEON_URL)
    with engine.connect() as conn:
        print("Connected to Neon")
        cases = conn.execute(text("SELECT COUNT(*) FROM cases")).scalar()
        events = conn.execute(text("SELECT COUNT(*) FROM case_events")).scalar()
        tasks = conn.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
        print(f"Neon -> Cases: {cases}, Events: {events}, Tasks: {tasks}")
except Exception as e:
    print(f"Neon Error: {e}")
