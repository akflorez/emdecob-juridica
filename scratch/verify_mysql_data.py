
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = pymysql.connect(
        host='127.0.0.1',
        user='emdecob',
        password='Emdecob2026*',
        database='emdecob_consultas'
    )
    cursor = conn.cursor()
    
    cursor.execute("SHOW TABLES")
    print("Tables in MySQL:", [t[0] for t in cursor.fetchall()])
    
    tables = ['cases', 'case_events', 'tasks']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count}")
        except:
            print(f"{table}: Not found")
            
    conn.close()
except Exception as e:
    print(f"Error MySQL: {e}")
