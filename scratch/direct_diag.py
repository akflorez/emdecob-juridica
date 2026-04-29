
import psycopg2
import os

try:
    # Try connecting to default postgres db
    conn = psycopg2.connect("postgresql://emdecob:emdecob2026@127.0.0.1:5432/postgres")
    print("Connected to 'postgres' db")
    conn.close()
except Exception as e:
    print(f"Error postgres db: {type(e).__name__}")
    try:
        msg = str(e).encode('latin-1', errors='replace').decode('utf-8', errors='replace')
        print(f"Decoded error: {msg}")
    except:
        print("Could not decode error")

try:
    # Try connecting to juricob
    conn = psycopg2.connect("postgresql://emdecob:emdecob2026@127.0.0.1:5432/juricob")
    print("Connected to 'juricob' db")
    conn.close()
except Exception as e:
    print(f"Error juricob db: {type(e).__name__}")
