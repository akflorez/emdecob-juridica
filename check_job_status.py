from sqlalchemy import create_engine, text
import os

db_url = 'mysql+pymysql://emdecob:Emdecob2026*@127.0.0.1:3306/emdecob_consultas'
engine = create_engine(db_url)

with engine.connect() as conn:
    row = conn.execute(text('SELECT id, status, total_items, processed_items, error_message FROM search_jobs ORDER BY id DESC LIMIT 1')).fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Status: {row[1]}")
        print(f"Progress: {row[3]}/{row[2]}")
        if row[4]:
            print(f"Error: {row[4]}")
    else:
        print("No jobs found.")
