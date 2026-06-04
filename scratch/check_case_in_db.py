import os
import sys

sys.path.append(os.getcwd())
from backend.db import SessionLocal
from backend.models import Case, CaseEvent
from backend.service.publicaciones import is_relevant_actuacion

def main():
    db = SessionLocal()
    try:
        rad = "11001400300720250052200"
        case = db.query(Case).filter(Case.radicado == rad).first()
        if not case:
            print(f"Case with radicado {rad} not found in DB!")
            return
            
        print(f"Case found: ID={case.id} | Radicado={case.radicado} | Demandante={case.demandante} | Demandado={case.demandado}")
        
        events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).all()
        print(f"Total events found in DB: {len(events)}")
        
        for idx, ev in enumerate(events):
            title = getattr(ev, "title", "")
            detail = getattr(ev, "detail", "")
            ev_date = getattr(ev, "event_date", "")
            is_rel = is_relevant_actuacion(title)
            print(f"[{idx+1:02d}] Date={ev_date} | Title={repr(title)} | Relevant={is_rel}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
