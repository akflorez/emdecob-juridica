from sqlalchemy import create_engine, text

url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
print(f"Connecting to database: {url}")
engine = create_engine(url)

# Open connection and start transaction block
with engine.connect() as conn:
    with conn.begin():
        # 1. Alter table to add columns
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(100) DEFAULT 'USER';"))
        print("Columns is_superadmin and role created successfully (inside transaction).")

        # 2. Update users
        email_to_update = 'direccionanaliticaemdecob@gmail.com'
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

# Open a new connection to inspect and verify the committed state
with engine.connect() as conn:
    res_select = conn.execute(text("SELECT id, email, username, company_id, is_admin, is_superadmin, role, is_active FROM users ORDER BY id;"))
    columns = res_select.keys()
    print("\nCommitted users state in emdecob_consultas:")
    for row in res_select:
        print(dict(zip(columns, row)))
