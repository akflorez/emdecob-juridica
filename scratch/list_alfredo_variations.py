
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Listing Alfredo lists...")
        lists = conn.execute(text("SELECT id, name FROM project_lists WHERE name ILIKE '%Alfredo%'")).fetchall()
        for l in lists:
            print(f"ID: {l[0]}, Name: '{l[1]}'")

except Exception as e:
    print(f"Error: {e}")
