
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    conn = psycopg2.connect(host="84.247.130.122", user="emdecob", password="emdecob2026", port="5432", database="postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    dbs = cursor.fetchall()
    print("Databases on Contabo:")
    for db in dbs:
        print(f"- {db[0]}")
    conn.close()
except Exception as e:
    print(f"Error listing DBs: {e}")
