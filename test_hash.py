import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("SELECT username, hashed_password FROM users WHERE username ILIKE '%cuartas%'")
users = cur.fetchall()

for u in users:
    print(f"User {u[0]}: {u[1][:20]}... (len: {len(u[1])})")
