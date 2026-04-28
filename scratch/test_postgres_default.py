
import psycopg2
def test_db(dbname):
    try:
        conn = psycopg2.connect(host="localhost", database=dbname, user="postgres", password="emdecob2026", port="5432")
        print(f"Success connecting to {dbname} as postgres")
        conn.close()
    except Exception as e:
        print(f"Fail {dbname}: {str(e).encode('ascii', 'ignore').decode('ascii')}")

test_db("postgres")
test_db("juricob")
