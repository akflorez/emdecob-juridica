
import sqlalchemy
from sqlalchemy import create_engine, text

URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
engine = create_engine(URL)

with engine.connect() as conn:
    # Cuantas tareas tienen parent_id (subtareas)?
    total = conn.execute(text("SELECT count(*) FROM tasks")).scalar()
    subtareas = conn.execute(text("SELECT count(*) FROM tasks WHERE parent_id IS NOT NULL")).scalar()
    padres = conn.execute(text("SELECT count(*) FROM tasks WHERE parent_id IS NULL")).scalar()
    
    print(f"Total tareas: {total}")
    print(f"Tareas principales (sin parent): {padres}")
    print(f"Subtareas (con parent_id): {subtareas}")
    
    # Muestra de subtareas
    if subtareas > 0:
        sample = conn.execute(text("""
            SELECT t.id, t.title, t.parent_id, t.status, p.title as parent_title
            FROM tasks t
            JOIN tasks p ON t.parent_id = p.id
            LIMIT 5
        """)).fetchall()
        print(f"\nMuestra de subtareas:")
        for r in sample:
            print(f"  Subtarea ID {r[0]}: '{r[1]}' -> Padre: '{r[4]}' (ID {r[2]})")
    else:
        print("\nNo hay subtareas con parent_id en la BD.")
        print("Verificando si las subtareas de ClickUp se guardaron de otra forma...")
        # Ver si hay clickup_id en las tareas padre
        sample = conn.execute(text("SELECT id, title, clickup_id, parent_id FROM tasks LIMIT 10")).fetchall()
        for r in sample:
            print(f"  ID {r[0]}: '{r[1]}' | clickup_id={r[2]} | parent_id={r[3]}")
