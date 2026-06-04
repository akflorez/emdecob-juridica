import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Checking emdecob_consultas database...")
        res = conn.execute(text("SELECT count(*) FROM cases"))
        print(f"Total cases: {res.scalar()}")
        
        # Search for case
        res = conn.execute(text("SELECT id, radicado, id_proceso, demandante, juzgado, has_documents FROM cases WHERE id_proceso = '93451451' OR radicado = '70001400300620180045500'"))
        cases = res.fetchall()
        print(f"Found {len(cases)} cases matching:")
        for c in cases:
            print(f"  ID: {c[0]} | Radicado: {c[1]} | ID Proceso: {c[2]} | demandante: {c[3]} | has_docs: {c[5]}")
            e_res = conn.execute(text("SELECT count(*) FROM case_events WHERE case_id = :cid"), {"cid": c[0]})
            print(f"    Events count: {e_res.scalar()}")
            
            # Print first 5 events
            e_rows = conn.execute(text("SELECT id, event_date, title, con_documentos, id_reg_actuacion FROM case_events WHERE case_id = :cid ORDER BY event_date DESC, id DESC LIMIT 5"), {"cid": c[0]})
            for er in e_rows.fetchall():
                print(f"      Event ID: {er[0]} | Date: {er[1]} | Title: {er[2]} | con_docs: {er[3]} | id_reg: {er[4]}")
            
except Exception as e:
    print(f"Error: {e}")
