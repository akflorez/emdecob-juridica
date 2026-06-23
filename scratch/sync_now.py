import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# We connect using SessionLocal
from backend.db import SessionLocal
from backend.models import Case, CaseEvent

db = SessionLocal()
try:
    radicado = '11001400304820250059500'
    cases = db.query(Case).filter(Case.radicado == radicado).all()
    print(f"Total cases with radicado {radicado}: {len(cases)}")
    for c in cases:
        ev_count = db.query(CaseEvent).filter(CaseEvent.case_id == c.id).count()
        print(f"ID={c.id}, CompanyID={c.company_id}, UserID={c.user_id}, EventsCount={ev_count}")
finally:
    db.close()
