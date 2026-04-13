import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url.startswith("mysql"):
    exit(0)

try:
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
        print("🔍 Verificando columna 'source_url' en 'case_publications'...")
        cursor.execute("SHOW COLUMNS FROM case_publications LIKE 'source_url'")
        if not cursor.fetchone():
            print("➕ Agregando columna 'source_url'...")
            cursor.execute("ALTER TABLE case_publications ADD COLUMN source_url TEXT NULL AFTER documento_url")
            print("🚀 Columna agregada.")
        else:
            print("ℹ️ La columna 'source_url' ya existe.")

    connection.commit()
    connection.close()
    print("✨ Migración de publicaciones completada.")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
