import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url.startswith("mysql"):
    print("❌ No es una base de datos MySQL. Saltando migración local.")
    exit(0)

# Extraer credenciales: mysql+pymysql://user:pass@host:port/db
try:
    # Eliminar el prefijo mysql+pymysql://
    conn_str = db_url.split("://")[1]
    auth_part, host_part = conn_str.split("@")
    user, password = auth_part.split(":")
    host_port, db_name = host_part.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 3306

    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        port=port
    )

    with connection.cursor() as cursor:
        print("🔍 Analizando índices de la tabla 'cases'...")
        cursor.execute("SHOW INDEX FROM cases WHERE Column_name = 'radicado' AND Non_unique = 0")
        unique_rad = cursor.fetchone()
        
        if unique_rad:
            idx_name = unique_rad[2]
            print(f"✅ Encontrado índice único '{idx_name}' en 'radicado'. Eliminando...")
            cursor.execute(f"ALTER TABLE cases DROP INDEX {idx_name}")
            print("🚀 Índice único eliminado.")
        else:
            print("ℹ️ No se encontró índice único en 'radicado' (quizás ya se eliminó).")

        print("🔍 Verificando columna 'id_proceso'...")
        cursor.execute("SHOW COLUMNS FROM cases LIKE 'id_proceso'")
        if not cursor.fetchone():
            print("➕ Agregando columna 'id_proceso'...")
            cursor.execute("ALTER TABLE cases ADD COLUMN id_proceso VARCHAR(20) NULL")
            print("🚀 Columna agregada.")
            
            print("➕ Agregando índice único a 'id_proceso'...")
            cursor.execute("CREATE UNIQUE INDEX ix_cases_id_proceso ON cases(id_proceso)")
            print("🚀 Índice único creado.")
        else:
            print("ℹ️ La columna 'id_proceso' ya existe.")

        print("➕ Asegurando que 'radicado' sea indexado (pero no único)...")
        cursor.execute("SHOW INDEX FROM cases WHERE Column_name = 'radicado'")
        if not cursor.fetchone():
            cursor.execute("CREATE INDEX ix_cases_radicado ON cases(radicado)")
            print("🚀 Índice simple creado para 'radicado'.")

    connection.commit()
    connection.close()
    print("✨ Migración completada exitosamente.")

except Exception as e:
    print(f"❌ Error durante la migración: {e}")
    exit(1)
