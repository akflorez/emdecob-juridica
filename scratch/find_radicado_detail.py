
import sqlalchemy
from sqlalchemy import create_engine, text

URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
engine = create_engine(URL)

with engine.connect() as conn:
    print("=== BUSCANDO EL RADICADO ESPECIFICO ===")
    radicado = '11001400302120200051200'
    res = conn.execute(text("SELECT id, title, clickup_id, parent_id FROM tasks WHERE title LIKE :r"), {"r": f"%{radicado}%"}).fetchall()
    
    if not res:
        print(f"No se encontro el radicado {radicado} en la base de datos.")
    else:
        for r in res:
            print(f"ID: {r[0]} | Title: {r[1]} | ClickUp ID: {r[2]} | Parent ID: {r[3]}")
            
            # Buscar sus subtareas
            subtasks = conn.execute(text("SELECT id, title FROM tasks WHERE parent_id = :p"), {"p": r[0]}).fetchall()
            print(f"  Subtareas encontradas en DB: {len(subtasks)}")
            for s in subtasks:
                print(f"    - {s[1]}")
            
            # Buscar sus checklists
            checklists = conn.execute(text("SELECT id, content, is_completed FROM task_checklist_items WHERE task_id = :p"), {"p": r[0]}).fetchall()
            print(f"  Checklist items encontrados en DB: {len(checklists)}")
            for cl in checklists:
                print(f"    - [{'x' if cl[2] else ' '}] {cl[1]}")
