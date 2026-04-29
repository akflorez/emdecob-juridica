import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Intentar extraer datos de la URL
url = os.getenv("DATABASE_URL")
if not url:
    print("DATABASE_URL no encontrada")
    exit(1)

print(f"Conectando a {url.split('@')[-1]}...")

try:
    # Forzar encoding a latin1 o utf8 si hay problemas
    conn = psycopg2.connect(url)
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()

    print("--- DIAGNOSTICO POSTGRES ---")

    # Usuarios
    cur.execute("SELECT id, username FROM users")
    users = cur.fetchall()
    for uid, uname in users:
        cur.execute("SELECT COUNT(*) FROM cases WHERE user_id = %s", (uid,))
        c_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tasks WHERE assignee_id = %s", (uid,))
        t_count = cur.fetchone()[0]
        print(f"User: {uname} (ID: {uid}) - Casos: {c_count} - Tareas: {t_count}")

    cur.execute("SELECT COUNT(*) FROM cases WHERE user_id IS NULL")
    orphans = cur.fetchone()[0]
    print(f"Casos huérfanos: {orphans}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
