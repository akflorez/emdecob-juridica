import os
import sys
import psycopg2
import bcrypt
from urllib.parse import urlparse
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_superadmin():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
        
    print(f"Connecting to database to create SuperAdmin...")
    result = urlparse(db_url)
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Verificar si el superadmin ya existe
    cursor.execute("SELECT id FROM users WHERE username = 'superadmin'")
    superadmin = cursor.fetchone()
    
    if superadmin:
        print("SuperAdmin ya existe.")
    else:
        # Pass hardcoded temporal: "admin123$" -> hay que cambiarla en prod
        hashed_pw = bcrypt.hashpw("admin123$".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # SuperAdmin no tiene company_id (company_id = NULL)
        cursor.execute(
            "INSERT INTO users (username, hashed_password, nombre, is_admin, is_active, company_id) VALUES (%s, %s, %s, %s, %s, NULL) RETURNING id",
            ('superadmin', hashed_pw, 'Global Super Admin', True, True)
        )
        sa_id = cursor.fetchone()[0]
        print(f"SuperAdmin creado exitosamente con ID {sa_id}.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_superadmin()
