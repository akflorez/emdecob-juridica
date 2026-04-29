"""
MIGRACION DE DATOS: Contabo → Docker interno de producción
Este script se ejecuta LOCALMENTE desde tu PC con acceso a ambas bases de datos.

ANTES DE CORRER: 
- El servidor de producción debe estar UP (sin 502)
- Necesitas la IP del servidor donde corre Coolify
"""
import sqlalchemy
from sqlalchemy import create_engine, text

# Base de datos ORIGEN (Contabo - tiene los datos reales)
CONTABO_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

# Base de datos DESTINO (Docker interno de producción)
# CAMBIA esta IP por la IP real de tu servidor Coolify
# Si Coolify expone el puerto 5432, usa esa IP aquí
PROD_IP = "TU_IP_SERVIDOR"  # ← CAMBIAR
PROD_URL = f"postgresql://emdecob:emdecob2026@{PROD_IP}:5432/juricob"

TABLES_TO_MIGRATE = [
    "workspaces",
    "folders", 
    "project_lists",
    "tasks",
    "task_comments",
    "task_attachments",
]

def migrate():
    print("Conectando a Contabo (origen)...")
    src = create_engine(CONTABO_URL)
    
    print(f"Conectando a producción en {PROD_IP} (destino)...")
    dst = create_engine(PROD_URL)
    
    with src.connect() as src_conn, dst.connect() as dst_conn:
        for table in TABLES_TO_MIGRATE:
            try:
                rows = src_conn.execute(text(f"SELECT * FROM {table}")).fetchall()
                print(f"  {table}: {len(rows)} filas encontradas en Contabo")
                
                if rows:
                    cols = src_conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' ORDER BY ordinal_position")).fetchall()
                    col_names = [c[0] for c in cols]
                    
                    # Borrar datos existentes en destino para esta tabla
                    dst_conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                    
                    # Insertar datos
                    col_str = ", ".join(col_names)
                    placeholders = ", ".join([f":{c}" for c in col_names])
                    insert_sql = text(f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})")
                    
                    data = [dict(zip(col_names, row)) for row in rows]
                    dst_conn.execute(insert_sql, data)
                    dst_conn.commit()
                    print(f"  ✅ {table}: {len(rows)} filas migradas")
                    
            except Exception as e:
                print(f"  ❌ Error en {table}: {e}")
    
    print("\nMigración completada.")

if __name__ == "__main__":
    migrate()
