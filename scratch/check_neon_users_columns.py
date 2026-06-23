from sqlalchemy import create_engine, text

url = "postgresql://neondb_owner:npg_eWCA1gPd0ryo@ep-icy-thunder-akkkr42v.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require"
print(f"Connecting to Neon DB: {url}")
try:
    engine = create_engine(url)
    with engine.connect() as conn:
        table_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            );
        """)).scalar()
        print(f"Table 'users' exists: {table_check}")
        if table_check:
            columns = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users';
            """)).fetchall()
            print("Columns:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
            # Print users count and a sample
            users = conn.execute(text("SELECT id, username, email FROM users ORDER BY id")).fetchall()
            print(f"Total users: {len(users)}")
            for u in users[:5]:
                print(f"  ID: {u[0]}, username: {u[1]}, email: {u[2]}")
except Exception as e:
    print(f"Error checking Neon DB: {e}")
