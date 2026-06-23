import os
from sqlalchemy import create_engine, text

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

def inspect_case_456():
    with engine.connect() as conn:
        case = conn.execute(text("SELECT id, radicado, demandante, demandado, company_id FROM cases WHERE id = 456")).fetchone()
        if case:
            print(f"Radicado: {case[1]}")
            print(f"Demandante: {case[2]}")
            print(f"Demandado: {case[3]}")
            print(f"Company ID: {case[4]}")
        else:
            print("Case 456 not found.")

if __name__ == "__main__":
    inspect_case_456()
