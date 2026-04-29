
import sqlalchemy
from sqlalchemy import create_engine, text

# El servidor de produccion es 84.247.130.122
# El Docker db expone el puerto 5432 externamente
PROD_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(PROD_URL, connect_args={"connect_timeout": 10})
    with engine.connect() as conn:
        print("=== ESTADO ACTUAL DE LA BASE DE DATOS DE PRODUCCION ===")
        
        tasks = conn.execute(text("SELECT count(*) FROM tasks")).scalar()
        print(f"Tareas: {tasks}")
        
        workspaces = conn.execute(text("SELECT count(*) FROM workspaces")).scalar()
        print(f"Workspaces: {workspaces}")
        
        cases = conn.execute(text("SELECT count(*) FROM cases")).scalar()
        print(f"Casos: {cases}")
        
        users = conn.execute(text("SELECT id, username, is_admin FROM users")).fetchall()
        print(f"Usuarios: {users}")
        
        # Ver si hay otras bases de datos en el servidor
        dbs = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false")).fetchall()
        print(f"Bases de datos disponibles: {[d[0] for d in dbs]}")
        
        if tasks > 0:
            sample = conn.execute(text("SELECT id, title, list_id, status FROM tasks LIMIT 3")).fetchall()
            print(f"Muestra de tareas: {sample}")

except Exception as e:
    print(f"Error conectando a produccion: {e}")
