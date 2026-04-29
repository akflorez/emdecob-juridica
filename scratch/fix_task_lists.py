
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("--- REPARACION DE VINCULOS DE TAREAS ---")
        
        # 1. Encontrar la lista de Alfredo que esta siendo usada en el Workspace ID 4
        # (Asumimos que el usuario ve el Workspace 4 'Emdecob Juridico')
        target_list = conn.execute(text("SELECT id FROM project_lists WHERE name ILIKE '%Alfredo%' ORDER BY id DESC LIMIT 1")).scalar()
        
        if target_list:
            print(f"Lista de Alfredo detectada: ID {target_list}")
            
            # 2. Mover todas las tareas de CUALQUIER lista de Alfredo a la lista activa
            # Buscamos listas que se llamen parecido
            old_lists = conn.execute(text("SELECT id FROM project_lists WHERE name ILIKE '%Alfredo%' AND id != :target"), {"target": target_list}).fetchall()
            old_ids = [r[0] for r in old_lists]
            
            if old_ids:
                print(f"Moviendo tareas de listas viejas {old_ids} a la lista nueva {target_list}...")
                conn.execute(text("UPDATE tasks SET list_id = :target WHERE list_id IN :olds"), {"target": target_list, "olds": tuple(old_ids)})
                conn.commit()
            
            # 3. EMERGENCIA: Si hay tareas que no tienen list_id o tienen uno inexistente, moverlas a la lista de Alfredo
            print("Vinculando tareas huerfanas a la lista principal...")
            conn.execute(text("UPDATE tasks SET list_id = :target WHERE list_id IS NULL OR list_id NOT IN (SELECT id FROM project_lists)"), {"target": target_list})
            conn.commit()
            
            print("Limpieza completada.")
        else:
            print("No se encontro ninguna lista de Alfredo.")

except Exception as e:
    print(f"Error: {e}")
