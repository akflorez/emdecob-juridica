
"""
Verificar si el PostgreSQL nativo permite conexiones desde Docker.
El Docker gateway en Linux es tipicamente 172.17.0.1
"""
import sqlalchemy
from sqlalchemy import create_engine, text
import subprocess

# Ver configuración de pg_hba.conf para saber si acepta conexiones externas
PROD_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(PROD_URL, connect_args={"connect_timeout": 10})
    with engine.connect() as conn:
        # Verificar que hay datos
        tasks = conn.execute(text("SELECT count(*) FROM tasks")).scalar()
        print(f"Tareas disponibles: {tasks}")
        
        # Ver la configuracion de conexiones de PostgreSQL
        pg_hba = conn.execute(text("""
            SELECT type, database, user_name, address, auth_method 
            FROM pg_hba_file_rules 
            LIMIT 20
        """)).fetchall()
        print(f"\nReglas pg_hba.conf:")
        for row in pg_hba:
            print(f"  {row}")
            
        # Ver en qué IPs escucha PostgreSQL
        listen = conn.execute(text("SHOW listen_addresses")).scalar()
        print(f"\nlisten_addresses: {listen}")

except Exception as e:
    print(f"Error: {e}")
