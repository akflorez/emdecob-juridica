from sqlalchemy import create_engine, text

url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
print(f"Connecting to database: {url}")
engine = create_engine(url)

with engine.connect() as conn:
    # 1. Alter table to add columns if they do not exist
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(100) DEFAULT 'USER';"))
        print("Columns is_superadmin and role checked/created in users table.")
    except Exception as e:
        print(f"Error altering table users: {e}")

    # 2. Update users
    email_to_update = 'direccionanaliticaemdecob@gmail.com'
    try:
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
        print(f"Updated {res.rowcount} users with email {email_to_update}")
    except Exception as e:
        print(f"Error updating user by email: {e}")

    try:
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
        print(f"Updated {res_sa.rowcount} users with username 'superadmin'")
    except Exception as e:
        print(f"Error updating user 'superadmin': {e}")

    # 3. Print final state
    res_select = conn.execute(text("SELECT id, email, username, company_id, is_admin, is_superadmin, role, is_active FROM users ORDER BY id;"))
    columns = res_select.keys()
    print("\nFinal state of users in emdecob_consultas:")
    for row in res_select:
        print(dict(zip(columns, row)))
