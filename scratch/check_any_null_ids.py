import sqlalchemy
from sqlalchemy import create_engine, text

URL_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(URL_EMDECOB)
    with engine.connect() as conn:
        query = """
            SELECT c.id, c.radicado, COUNT(e.id) as count_null_ids
            FROM cases c
            JOIN case_events e ON c.id = e.case_id
            WHERE e.con_documentos = True AND e.id_reg_actuacion IS NULL
            GROUP BY c.id, c.radicado
            ORDER BY count_null_ids DESC
        """
        rows = conn.execute(text(query)).fetchall()
        print(f"Cases with missing id_reg_actuacion for document events: {len(rows)}")
        for r in rows[:10]:
            print(f"Case ID={r[0]} | Radicado={r[1]} | Missing count={r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
