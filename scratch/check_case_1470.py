import sqlalchemy
from sqlalchemy import create_engine, text

URL_JURICOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
URL_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

def check_db(url, name):
    print(f"\n=== DATABASE: {name} ===")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            # Look up case by radicado
            c = conn.execute(text("SELECT id, radicado, has_documents, last_check_at FROM cases WHERE radicado = '70001400300620180045500'")).fetchone()
            if not c:
                print("Case not found by radicado")
                return
            
            c_id = c[0]
            print(f"Case found: id={c[0]}, radicado={c[1]}, has_documents={c[2]}, last_check_at={c[3]}")
            
            # Count total events
            total_events = conn.execute(text("SELECT COUNT(*) FROM case_events WHERE case_id = :cid"), {"cid": c_id}).scalar()
            print(f"Total events: {total_events}")
            
            # Count events con_documentos = True
            con_docs_total = conn.execute(text("SELECT COUNT(*) FROM case_events WHERE case_id = :cid AND con_documentos = True"), {"cid": c_id}).scalar()
            
            # Count events with con_documentos = True and id_reg_actuacion is Null
            con_docs_no_id = conn.execute(text("SELECT COUNT(*) FROM case_events WHERE case_id = :cid AND con_documentos = True AND id_reg_actuacion IS NULL"), {"cid": c_id}).scalar()
            
            print(f"Events con_documentos=True: {con_docs_total}")
            print(f"Events con_documentos=True but id_reg_actuacion IS NULL: {con_docs_no_id}")
            
            # Show a sample of events
            sample = conn.execute(text("SELECT id, event_date, title, con_documentos, id_reg_actuacion FROM case_events WHERE case_id = :cid ORDER BY event_date DESC LIMIT 5"), {"cid": c_id}).fetchall()
            print("Sample events:")
            for s in sample:
                print(f"  id={s[0]} | date={s[1]} | title={s[2]} | con_doc={s[3]} | id_reg={s[4]}")
                
    except Exception as e:
        print(f"Error checking {name}: {e}")

check_db(URL_JURICOB, "juricob")
check_db(URL_EMDECOB, "emdecob_consultas")
