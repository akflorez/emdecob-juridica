
import sys
import os
sys.path.append(os.getcwd())

from backend.db import SessionLocal
from backend.models import Task, Case, User
from sqlalchemy import or_, and_

db = SessionLocal()
try:
    radicado = "63001400300320120025900"
    
    # Mock current_user as jurico_emdecob (ID 2 in DB)
    current_user_id = 2
    current_user = db.query(User).filter(User.id == current_user_id).first()
    
    query = db.query(Task)
    
    # Apply filters as in main.py
    if not current_user.is_admin:
        if current_user.username == "jurico_emdecob":
            query = query.join(Case, Task.case_id == Case.id, isouter=True)
            query = query.filter(or_(
                Task.assignee_id == current_user.id,
                Case.user_id == current_user.id
            ))
            
    if radicado:
        # Note: if current_user.is_admin is False, it already joined once.
        # Line 4066 joins again.
        query = query.join(Case, Task.case_id == Case.id, isouter=True)
        query = query.filter(or_(
            Case.radicado == radicado,
            Task.title.contains(radicado),
            Task.description.contains(radicado)
        ))
    
    print("Executing query...")
    tasks = query.all()
    print(f"Found {len(tasks)} tasks")
    for t in tasks:
        print(f"- {t.title}")
        
except Exception as e:
    print(f"QUERY ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
