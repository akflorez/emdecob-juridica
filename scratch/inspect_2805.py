import os
from sqlalchemy import create_engine, text

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

def inspect_2805():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, case_id, fecha_publicacion, estado_validacion, match_score, requiere_revision, texto_fuente_principal, url_fuente_principal FROM case_publications WHERE id = 2805")).fetchone()
        if res:
            print(f"ID: {res[0]}")
            print(f"Case ID: {res[1]}")
            print(f"Fecha: {res[2]}")
            print(f"Estado: {res[3]}")
            print(f"Score: {res[4]}")
            print(f"Req revision: {res[5]}")
            print(f"URL: {res[7]}")
            print(f"Text content length: {len(res[6]) if res[6] else 0}")
            print(f"Text snippet: {res[6][:300] if res[6] else ''}")
        else:
            print("Publication 2805 not found.")

if __name__ == "__main__":
    inspect_2805()
