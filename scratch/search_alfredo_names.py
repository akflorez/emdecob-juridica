
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Searching for Alfredo's name variations...")
        names = conn.execute(text("SELECT DISTINCT abogado FROM cases WHERE abogado ILIKE '%ALFREDO%'")).fetchall()
        print(f"Found names: {[n[0] for n in names]}")
        
        # Also check for tasks mentioning Alfredo
        tasks = conn.execute(text("SELECT id, title FROM tasks WHERE title ILIKE '%ALFREDO%' OR description ILIKE '%ALFREDO%' LIMIT 5")).fetchall()
        print(f"Sample tasks: {[(t[0], t[1]) for t in tasks]}")

except Exception as e:
    print(f"Error: {e}")
