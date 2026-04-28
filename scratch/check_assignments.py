import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_eWCA1gPd0ryo@ep-icy-thunder-akkkr42v.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require"

print(f"Connecting to Neon DB...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Successfully connected!")
        
        # Check users
        res = conn.execute(text("SELECT id, username, nombre, is_admin FROM users"))
        print("Users in DB:")
        for row in res:
            print(f"ID: {row[0]}, Username: {row[1]}, Name: {row[2]}, Admin: {row[3]}")
        
        # Check if cases are assigned
        res = conn.execute(text("SELECT user_id, count(*) FROM cases GROUP BY user_id"))
        print("Cases per User ID:")
        for row in res:
            print(f"User ID: {row[0]}, Count: {row[1]}")

        # Check if tasks are assigned
        res = conn.execute(text("SELECT assignee_id, count(*) FROM tasks GROUP BY assignee_id"))
        print("Tasks per Assignee ID:")
        for row in res:
            print(f"Assignee ID: {row[0]}, Count: {row[1]}")
            
except Exception as e:
    print(f"Connection failed: {e}")
