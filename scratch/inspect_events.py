import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

radicado = '11001400304820250059500'

with engine.connect() as conn:
    # Get case ID
    case_id = conn.execute(text("SELECT id FROM cases WHERE radicado = :rad").bindparams(rad=radicado)).scalar()
    print(f"Case ID for {radicado}: {case_id}")
    
    if case_id:
        # Get all events
        events = conn.execute(text("SELECT id, title, event_date FROM case_events WHERE case_id = :cid").bindparams(cid=case_id)).fetchall()
        print(f"Total events found: {len(events)}")
        for ev in events:
            print(ev)
            
        # Check relevancy
        from backend.service.publicaciones import is_relevant_actuacion
        print("\nChecking relevancy of each event:")
        for ev in events:
            rel = is_relevant_actuacion(ev[1])
            print(f"Title: {ev[1]} -> Relevant: {rel}")
