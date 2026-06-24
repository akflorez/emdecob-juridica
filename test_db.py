import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("SELECT id, username, nombre, is_active FROM users WHERE username = 'julian.cuartas'")
print("julian.cuartas:", cur.fetchall())
