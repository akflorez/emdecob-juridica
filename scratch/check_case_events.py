import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Checking duplicate cases for radicado '70001400300620180045500'...")
        res = conn.execute(text("SELECT id, radicado, juzgado, id_proceso FROM cases WHERE radicado = '70001400300620180045500'"))
        cases = res.fetchall()
        print(f"Found {len(cases)} cases:")
        for c in cases:
            print(f"  ID: {c[0]} | Juzgado: {c[2]} | ID Proceso: {c[3]}")
            # Count events for each
            e_res = conn.execute(text("SELECT count(*) FROM case_events WHERE case_id = :cid"), {"cid": c[0]})
            print(f"    Events count: {e_res.scalar()}")
            
except Exception as e:
    print(f"Error: {e}")
