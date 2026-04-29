
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
rad = "63001400300320120025900"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id FROM cases WHERE radicado = :rad"), {"rad": rad}).first()
        if res:
            case_id = res[0]
            print(f"Case ID for {rad}: {case_id}")
            tasks = conn.execute(text("SELECT id, title, case_id FROM tasks WHERE case_id = :cid"), {"cid": case_id}).fetchall()
            print(f"Tasks for this case: {len(tasks)}")
            for t in tasks:
                print(f"- {t[1]} (ID: {t[0]})")
        else:
            print(f"Case {rad} not found")
except Exception as e:
    print(f"Error: {e}")
