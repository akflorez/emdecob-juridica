
import psycopg2
import os

try:
    conn = psycopg2.connect("postgresql://emdecob:emdecob2026@127.0.0.1:5432/postgres")
    cursor = conn.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    dbs = cursor.fetchall()
    print("Databases in Postgres:", [db[0] for db in dbs])
    conn.close()
except Exception as e:
    print(f"Error: {e}")
