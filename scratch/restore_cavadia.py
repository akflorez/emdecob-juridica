
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("--- RESTAURACION DE TAREAS DE CAVADIA ---")
        
        # 1. Devolver tareas de 4829 (Bernal) a 26 (Cavadia)
        # Esto es lo que movimos por error
        print("Restaurando tareas al ID 26 (Alfredo Eduardo Cavadia Sanchez)...")
        conn.execute(text("UPDATE tasks SET list_id = 26 WHERE list_id = 4829"))
        conn.commit()
        
        # 2. Verificar el conteo final
        count = conn.execute(text("SELECT count(*) FROM tasks WHERE list_id = 26")).scalar()
        print(f"Tareas finales en Cavadia (ID 26): {count}")
        
        # 3. Ver si hay mas Alfredos que tengan tareas y unirlos SOLAMENTE si el nombre es IGUAL
        print("Buscando otras carpetas EXACTAS de Cavadia...")
        others = conn.execute(text("SELECT id FROM project_lists WHERE name = 'ALFREDO EDUARDO CAVADIA SANCHEZ' AND id != 26")).fetchall()
        for (oid,) in others:
            print(f"Fusionando carpeta duplicada {oid} -> 26")
            conn.execute(text("UPDATE tasks SET list_id = 26 WHERE list_id = :oid"), {"oid": oid})
        
        conn.commit()
        print("Restauracion completada.")

except Exception as e:
    print(f"Error: {e}")
