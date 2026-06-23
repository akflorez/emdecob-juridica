import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

with engine.connect() as conn:
    text_content = conn.execute(text("SELECT texto_fuente_principal FROM case_publications WHERE id = 2805")).scalar()
    lines = text_content.split('\n')
    for idx in range(max(0, 560), min(len(lines), 585)):
        print(f"L{idx}: {lines[idx]}")
