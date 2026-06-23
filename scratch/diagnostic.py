import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
engine = create_engine(url)

with engine.connect() as conn:
    print("--- 1. REAL COMPANIES ---")
    try:
        res = conn.execute(text("SELECT * FROM companies ORDER BY id;"))
        cols = res.keys()
        print(f"Columns: {list(cols)}")
        for row in res:
            print(dict(zip(cols, row)))
    except Exception as e:
        print(f"Error querying companies: {e}")

    print("\n--- 2. CASES COLUMNS ---")
    try:
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'cases';"))
        for row in res:
            print(f"  {row[0]}: {row[1]}")
    except Exception as e:
        print(f"Error querying cases columns: {e}")

    print("\n--- 3. CASES DISTRIBUTION BY USER AND COMPANY ---")
    try:
        # Check if user_id or created_by exists
        res_cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'cases';")).fetchall()
        case_cols = [r[0] for r in res_cols]
        
        user_col = "user_id"
        if "created_by" in case_cols:
            user_col = "created_by"
        elif "created_by_user_id" in case_cols:
            user_col = "created_by_user_id"
        
        print(f"Using owner column: '{user_col}'")
        
        query = f"""
            SELECT {user_col}, company_id, COUNT(*) 
            FROM cases 
            GROUP BY {user_col}, company_id 
            ORDER BY {user_col}, company_id;
        """
        res = conn.execute(text(query))
        for row in res:
            print(f"  Owner ({user_col}): {row[0]} | Company ID: {row[1]} | Count: {row[2]}")
            
    except Exception as e:
        print(f"Error querying cases distribution: {e}")

    print("\n--- 4. USERS ---")
    try:
        res = conn.execute(text("SELECT id, username, email, company_id, is_admin, is_superadmin, role FROM users ORDER BY id;"))
        cols = res.keys()
        for row in res:
            print(dict(zip(cols, row)))
    except Exception as e:
        print(f"Error querying users: {e}")
