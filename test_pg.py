import psycopg2

try:
    conn = psycopg2.connect(
        dbname="emdecob_consultas",
        user="emdecob",
        password="emdecob2026",
        host="127.0.0.1",
        port=5432
    )
    print("SUCCESSFULLY CONNECTED to emdecob_consultas!")
    conn.close()
except UnicodeDecodeError as e:
    raw = e.args[1]
    err_msg = raw.decode('cp1252', errors='replace')
    print("FAILED with UnicodeDecodeError:", err_msg.strip())
except Exception as e:
    print("FAILED:", str(e).strip())
