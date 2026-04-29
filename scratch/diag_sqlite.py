import sqlite3
import os

db_path = "backend/database.db"
if not os.path.exists(db_path):
    print(f"No existe {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- DIAGNOSTICO SQLITE ---")

# Listar usuarios
cursor.execute("SELECT id, username FROM users")
users = cursor.fetchall()
for uid, uname in users:
    cursor.execute("SELECT COUNT(*) FROM cases WHERE user_id = ?", (uid,))
    count = cursor.fetchone()[0]
    print(f"Usuario: {uname} (ID: {uid}) - Casos: {count}")

cursor.execute("SELECT COUNT(*) FROM cases WHERE user_id IS NULL")
orphans = cursor.fetchone()[0]
print(f"Casos huérfanos: {orphans}")

cursor.execute("SELECT COUNT(*) FROM case_events")
events = cursor.fetchone()[0]
print(f"Total actuaciones: {events}")

conn.close()
