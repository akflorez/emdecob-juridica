import sqlite3
import os

# Probamos todas las rutas posibles de bases de datos
bases = ["backend/database.db", "backend/juricob.db", "database.db"]

for b in bases:
    if os.path.exists(b):
        try:
            conn = sqlite3.connect(b)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT radicado) FROM case_events")
            count, distinct = cur.fetchone()[0], cur.fetchone()[1]
            print(f"Base: {b} - Total Actuaciones: {count} - Radicados Distintos: {distinct}")
            
            cur.execute("SELECT radicado FROM case_events LIMIT 5")
            print(f"Ejemplos de radicados en acts: {cur.fetchall()}")
            
            cur.execute("SELECT radicado FROM cases LIMIT 5")
            print(f"Ejemplos de radicados en casos: {cur.fetchall()}")
            
            conn.close()
        except Exception as e:
            print(f"Error en {b}: {e}")
