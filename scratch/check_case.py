
import psycopg2
conn = psycopg2.connect('postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob')
cur = conn.cursor()
cur.execute("SELECT id, demandante, demandado FROM cases WHERE radicado = '11001400302420240140300'")
print(cur.fetchone())
conn.close()
