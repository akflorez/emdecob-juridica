
import sqlalchemy
from sqlalchemy import create_engine, text

DB_JURICOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
DB_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

def migrate():
    engine_j = create_engine(DB_JURICOB)
    engine_e = create_engine(DB_EMDECOB)
    
    print("Starting Optimized Master Merge...")
    
    with engine_e.connect() as conn_e:
        cases_e = conn_e.execute(text("SELECT radicado, demandado, demandante, juzgado, user_id, fecha_radicacion, alias, has_documents, cedula, abogado FROM cases")).fetchall()
        
        with engine_j.connect() as conn_j:
            existing_radicados = {r[0] for r in conn_j.execute(text("SELECT radicado FROM cases")).fetchall()}
            
            added_cases = 0
            for i, c in enumerate(cases_e):
                if c[0] not in existing_radicados:
                    uid = c[4]
                    if uid == 20: uid = 2
                    
                    conn_j.execute(text("""
                        INSERT INTO cases (radicado, demandado, demandante, juzgado, user_id, fecha_radicacion, alias, has_documents, cedula, abogado, created_at, updated_at)
                        VALUES (:rad, :dem, :dmt, :juz, :uid, :fec, :ali, :doc, :ced, :abo, NOW(), NOW())
                    """), {
                        "rad": c[0], "dem": c[1], "dmt": c[2], "juz": c[3], "uid": uid,
                        "fec": c[5], "ali": c[6], "doc": c[7], "ced": c[8], "abo": c[9]
                    })
                    added_cases += 1
                    
                if i % 100 == 0:
                    conn_j.commit()
                    print(f"Processed {i}/{len(cases_e)} cases...")

            conn_j.commit()
            print(f"Added {added_cases} new cases.")
            
            print("Re-linking tasks...")
            conn_j.execute(text("""
                UPDATE tasks t
                SET case_id = c.id
                FROM cases c
                WHERE t.case_id IS NULL
                AND (
                    t.title ILIKE '%' || c.radicado || '%' 
                    OR (c.demandado IS NOT NULL AND c.demandado != '' AND t.title ILIKE '%' || c.demandado || '%')
                )
            """))
            conn_j.commit()
            print("Master Merge completed.")

if __name__ == "__main__":
    migrate()
