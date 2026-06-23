import sqlalchemy
from sqlalchemy import create_engine, text

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

with engine.connect() as conn:
    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    print("Tables in emdecob_consultas:")
    print([t[0] for t in tables])
