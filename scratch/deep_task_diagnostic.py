
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("--- DIAGNOSTICO DE TAREAS ---")
        
        # 1. Ver una muestra de tareas
        tasks = conn.execute(text("SELECT id, title, list_id, status FROM tasks LIMIT 5")).fetchall()
        print(f"Muestra de tareas: {tasks}")
        
        # 2. Ver si hay tareas para la lista 26 (Alfredo)
        alfredo_tasks = conn.execute(text("SELECT count(*) FROM tasks WHERE list_id = 26")).scalar()
        print(f"Tareas en Lista 26 (Alfredo): {alfredo_tasks}")
        
        # 3. Ver si hay tareas con list_id que NO EXISTE en project_lists
        orphans = conn.execute(text("SELECT count(*) FROM tasks WHERE list_id NOT IN (SELECT id FROM project_lists)")).scalar()
        print(f"Tareas huerfanas (ID de lista inexistente): {orphans}")
        
        # 4. Ver los estados disponibles
        statuses = conn.execute(text("SELECT status, count(*) FROM tasks GROUP BY status")).fetchall()
        print(f"Estados en DB: {statuses}")

except Exception as e:
    print(f"Error: {e}")
