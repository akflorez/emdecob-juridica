
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM cases")
    cases_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM case_events")
    events_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks")
    tasks_count = cursor.fetchone()[0]
    
    print(f"Cases: {cases_count}")
    print(f"Case Events (Actuaciones): {events_count}")
    print(f"Tasks (Tareas): {tasks_count}")
    
    if cases_count > 0:
        cursor.execute("SELECT radicado, demandado FROM cases LIMIT 5")
        print("\nSample Cases:")
        for row in cursor.fetchall():
            print(f"- {row[0]}: {row[1]}")
            
    conn.close()
except Exception as e:
    print(f"Error connecting to Postgres: {e}")
