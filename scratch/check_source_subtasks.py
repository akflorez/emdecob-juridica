
import sqlalchemy
from sqlalchemy import create_engine, text

URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
engine = create_engine(URL)

with engine.connect() as conn:
    print("=== VERIFICANDO SUBTAREAS Y CHECKLISTS EN ORIGEN ===")
    
    # 1. Subtareas (parent_id)
    subtasks = conn.execute(text("SELECT count(*) FROM tasks WHERE parent_id IS NOT NULL")).scalar()
    print(f"Subtareas en origen (parent_id): {subtasks}")
    
    # 2. Checklist items
    try:
        checklists = conn.execute(text("SELECT count(*) FROM task_checklist_items")).scalar()
        print(f"Checklist items en origen: {checklists}")
    except Exception as e:
        print(f"Error consultando checklists: {e}")
        
    # 3. Ver una tarea que tenga algo para entender la estructura
    if subtasks > 0:
        sample = conn.execute(text("SELECT id, title, parent_id FROM tasks WHERE parent_id IS NOT NULL LIMIT 5")).fetchall()
        for r in sample:
            print(f"  Subtarea: {r[1]} (Parent ID: {r[2]})")
    
    if checklists > 0:
        sample = conn.execute(text("SELECT task_id, content FROM task_checklist_items LIMIT 5")).fetchall()
        for r in sample:
            print(f"  Checklist Item: {r[1]} (Task ID: {r[0]})")
