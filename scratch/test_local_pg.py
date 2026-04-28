
import psycopg2
try:
    conn = psycopg2.connect(
        host="localhost",
        database="juricob",
        user="emdecob",
        password="emdecob2026",
        port="5432"
    )
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
