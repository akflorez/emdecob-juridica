import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

with engine.connect() as conn:
    # Query indexes on case_publications
    query = text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'case_publications'
    """)
    res = conn.execute(query).fetchall()
    print("Indexes on case_publications:")
    for row in res:
        print(row)
