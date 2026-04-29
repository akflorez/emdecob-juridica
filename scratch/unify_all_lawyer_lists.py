
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("--- UNIFICACION MASIVA DE CARPETAS DE ABOGADOS ---")
        
        # 1. Obtener todos los nombres de listas únicos
        names = conn.execute(text("SELECT DISTINCT name FROM project_lists")).fetchall()
        
        for (name,) in names:
            if not name: continue
            
            # 2. Para cada nombre, encontrar el ID más reciente (el que probablemente se ve en pantalla)
            all_ids = conn.execute(text("SELECT id FROM project_lists WHERE name = :n ORDER BY id DESC"), {"n": name}).fetchall()
            ids = [r[0] for r in all_ids]
            
            if len(ids) > 1:
                target = ids[0]
                olds = ids[1:]
                print(f"Unificando '{name}': Movinedo tareas de {olds} -> {target}")
                conn.execute(text("UPDATE tasks SET list_id = :target WHERE list_id IN :olds"), {"target": target, "olds": tuple(olds)})
                
        conn.commit()
        print("Unificacion completada con exito.")

except Exception as e:
    print(f"Error: {e}")
