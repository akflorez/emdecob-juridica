import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
engine = create_engine(url)

with engine.connect() as conn:
    print("\n=== Columns in 'cases' ===")
    res = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'cases'
        ORDER BY ordinal_position;
    """))
    for row in res:
        print(f"{row[0]}: {row[1]}")
