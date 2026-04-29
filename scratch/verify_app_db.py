
import sys
import os
sys.path.append(os.getcwd())

from backend.db import SessionLocal
from backend.models import Case, CaseEvent, Task

db = SessionLocal()
try:
    cases_count = db.query(Case).count()
    events_count = db.query(CaseEvent).count()
    tasks_count = db.query(Task).count()
    
    print(f"Connected to DB via backend.db")
    print(f"Cases: {cases_count}")
    print(f"Case Events (Actuaciones): {events_count}")
    print(f"Tasks (Tareas): {tasks_count}")
    
    if cases_count > 0:
        c = db.query(Case).first()
        print(f"\nSample Case: {c.radicado} - {c.demandado}")
        
finally:
    db.close()
