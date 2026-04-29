
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("--- LIMPIEZA PROFUNDA Y UNIFICACION DE CARPETAS ---")
        
        # 1. Obtener todas las listas con sus nombres limpios
        all_lists = conn.execute(text("SELECT id, TRIM(name) as clean_name FROM project_lists")).fetchall()
        
        # Agrupar por nombre limpio
        groups = {}
        for lid, name in all_lists:
            if not name: continue
            name = name.upper() # Unificar a mayusculas
            if name not in groups: groups[name] = []
            groups[name].append(lid)
            
        for name, ids in groups.items():
            if len(ids) > 1:
                target = ids[0]
                olds = ids[1:]
                print(f"Fusionando '{name}': {len(olds)} duplicados -> ID {target}")
                
                # Mover tareas
                conn.execute(text("UPDATE tasks SET list_id = :target WHERE list_id IN :olds"), {"target": target, "olds": tuple(olds)})
                
                # Opcional: Podriamos borrar las listas viejas, pero por seguridad solo movemos las tareas por ahora
                
        conn.commit()
        print("Limpieza completada.")

except Exception as e:
    print(f"Error: {e}")
