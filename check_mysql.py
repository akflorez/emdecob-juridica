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
        cursor.execute("SELECT count(*) FROM cases")
        count = cursor.fetchone()[0]
        print(f"Total cases in MySQL: {count}")
finally:
    conn.close()
