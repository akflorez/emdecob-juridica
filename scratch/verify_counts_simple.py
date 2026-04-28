import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@localhost:5432/juricob"

engine = create_engine(DATABASE_URL)

def check_counts():
    try:
        with engine.connect() as conn:
            # Check cases
            res = conn.execute(text("SELECT count(*) FROM cases"))
            print(f"Cases count: {res.scalar()}")

            # Check case_events (actuaciones)
            res = conn.execute(text("SELECT count(*) FROM case_events"))
            print(f"CaseEvents (Actuaciones) count: {res.scalar()}")

            # Check tasks (tareas)
            res = conn.execute(text("SELECT count(*) FROM tasks"))
            print(f"Tasks count: {res.scalar()}")

            # Check workspaces
            res = conn.execute(text("SELECT count(*) FROM workspaces"))
            print(f"Workspaces count: {res.scalar()}")

            # Sample case_events to see if they have data
            if res.scalar() > 0:
                res = conn.execute(text("SELECT detail FROM case_events LIMIT 5"))
                for row in res:
                    print(f"Event detail sample: {str(row[0])[:50]}...")

    except Exception as e:
        print(f"Error: {str(e).encode('ascii', 'ignore').decode('ascii')}")

if __name__ == "__main__":
    check_counts()
