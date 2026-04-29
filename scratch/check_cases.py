
import sqlite3
import os

# Try common locations
paths = [
    os.path.join('backend', 'database.db'),
    os.path.join('..', 'backend', 'database.db'),
    'database.db'
]

db_path = None
for p in paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print("DB not found")
    exit(1)

print(f"Using DB: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List tables to be sure
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

cursor.execute("SELECT radicado, demandado FROM cases LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(f"Radicado: {row[0]}, Demandado: {row[1]}")
conn.close()
