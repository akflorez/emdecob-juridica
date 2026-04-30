from backend.db import SessionLocal
from backend.models import Task
import sys

db = SessionLocal()
try:
    tasks = db.query(Task).all()
    print(f"Total tasks in DB: {len(tasks)}")
    subtasks = [t for t in tasks if t.parent_id is not None]
    print(f"Total subtasks (with parent_id): {len(subtasks)}")
    for s in subtasks[:10]:
        print(f" - Subtask ID {s.id}: '{s.title}' -> Parent ID {s.parent_id}")
finally:
    db.close()
