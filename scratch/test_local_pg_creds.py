
import psycopg2
try:
    conn = psycopg2.connect(host="localhost", database="juricob", user="emdecob", password="Emdecob2026*", port="5432")
    print("Success with MySQL password!")
    conn.close()
except Exception as e:
    print(f"Error MySQL Pass: {str(e).encode('ascii', 'ignore').decode('ascii')}")

try:
    conn = psycopg2.connect(host="localhost", database="juricob", user="emdecob", password="emdecob2026", port="5432")
    print("Success with docker password!")
    conn.close()
except Exception as e:
    print(f"Error Docker Pass: {str(e).encode('ascii', 'ignore').decode('ascii')}")
