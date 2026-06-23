import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
print(f"Connecting to database: {url}")
engine = create_engine(url)

with engine.connect() as conn:
    # 1. Check if users has the columns (should have them)
    # 2. Update the user with email 'direccionanaliticaemdecob@gmail.com'
    email_to_update = 'direccionanaliticaemdecob@gmail.com'
    print(f"Updating superadmin user with email: {email_to_update}")
    
    # Try altering columns just in case
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(100) DEFAULT 'USER';"))
        print("Columns checked/created.")
    except Exception as e:
        print(f"Error altering columns: {e}")

    # Run update
    res = conn.execute(text("""
        UPDATE users
        SET 
            is_superadmin = TRUE,
            is_admin = TRUE,
            company_id = NULL,
            role = 'SUPERADMIN',
            is_active = TRUE
        WHERE email = :email;
    """), {"email": email_to_update})
    print(f"Rows updated: {res.rowcount}")
    
    # Also update 'superadmin' username user just to be safe
    res_sa = conn.execute(text("""
        UPDATE users
        SET 
            is_superadmin = TRUE,
            is_admin = TRUE,
            company_id = NULL,
            role = 'SUPERADMIN',
            is_active = TRUE
        WHERE username = 'superadmin';
    """))
    print(f"Superadmin username user rows updated: {res_sa.rowcount}")
    
    # Check results
    res_select = conn.execute(text("SELECT id, email, username, company_id, is_admin, is_superadmin, role, is_active FROM users ORDER BY id;"))
    columns = res_select.keys()
    for row in res_select:
        print(dict(zip(columns, row)))
