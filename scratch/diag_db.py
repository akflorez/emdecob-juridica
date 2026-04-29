import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Case, Task, User, CaseEvent

# Use the path from the .env if available, or default to local sqlite/postgres
# In the workspace, it seems to use sqlite database.db or postgres juricob
# Let's check which one is used by main.py

import sys
sys.path.append(os.getcwd())
from backend.db import SessionLocal

db = SessionLocal()

print("--- DIAGNOSTICO DE USUARIOS Y DATOS ---")

users = db.query(User).all()
for u in users:
    case_count = db.query(Case).filter(Case.user_id == u.id).count()
    task_count = db.query(Task).filter(Task.assignee_id == u.id).count()
    task_by_case_owner = db.query(Task).join(Case).filter(Case.user_id == u.id).count()
    
    print(f"Usuario: {u.username} (ID: {u.id})")
    print(f"  - Casos asignados: {case_count}")
    print(f"  - Tareas asignadas: {task_count}")
    print(f"  - Tareas por propiedad de caso: {task_by_case_owner}")
    print("-" * 30)

orphans = db.query(Case).filter(Case.user_id == None).count()
print(f"Casos huérfanos (sin usuario): {orphans}")

total_events = db.query(CaseEvent).count()
print(f"Total actuaciones en BD: {total_events}")

db.close()
