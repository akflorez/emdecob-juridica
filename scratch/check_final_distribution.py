
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT user_id, COUNT(*) FROM cases GROUP BY user_id")).fetchall()
        print("User distribution in juricob cases:")
        for r in res:
            print(f"- User ID: {r[0]} | Count: {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
