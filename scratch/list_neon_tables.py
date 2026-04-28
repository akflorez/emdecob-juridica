
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
neon = os.getenv("NEON_URL")
engine = create_engine(neon)

with engine.connect() as conn:
    r = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
    tables = [row[0] for row in r]
    print(f"Tables in NEON: {len(tables)}")
    for t in sorted(tables):
        print(f"- {t}")
