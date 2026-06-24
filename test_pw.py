import os
import psycopg2
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()
url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cur.execute("SELECT id, username, hashed_password FROM users WHERE username = 'julian.cuartas'")
users = cur.fetchall()

for u in users:
    is_valid = pwd_context.verify('292509', u[2])
    print(f"User ID {u[0]} ({u[1]}): password '292509' valid? {is_valid}")
