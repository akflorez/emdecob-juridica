import os
from sqlalchemy import text
from backend.db import engine

def test_migrations():
    with open('backend/migration_queries.sql', 'r', encoding='utf-8') as f:
        queries = f.read().splitlines()

    with engine.connect() as conn:
        for q in queries:
            if q.strip():
                try:
                    conn.execute(text(q.strip()))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print(f"Error executing {q.strip()}: {e}")

if __name__ == "__main__":
    test_migrations()
