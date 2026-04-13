import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB"),
    port=int(os.getenv("MYSQL_PORT", 3306))
)

try:
    with conn.cursor() as cursor:
        cursor.execute("DESCRIBE cases")
        columns = cursor.fetchall()
        print("Columns in cases table:")
        for col in columns:
            print(col)
            
        cursor.execute("DESCRIBE case_events")
        columns = cursor.fetchall()
        print("\nColumns in case_events table:")
        for col in columns:
            print(col)
finally:
    conn.close()
