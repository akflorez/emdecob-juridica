import sqlite3
import asyncio
import httpx
import os

db_path = os.path.join("backend", "juricob.db")
if not os.path.exists(db_path):
    # try postgres
    import psycopg2
    try:
        conn = psycopg2.connect("postgresql://postgres:postgres@localhost/juricob") # assuming default
        c = conn.cursor()
        c.execute("SELECT radicado FROM cases WHERE demandado ILIKE '%AUGUSTO PAVANI%'")
        rad = c.fetchone()[0]
        print("Found Radicado Postgres:", rad)
    except:
        rad = "110013103033202500xxx00"
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT radicado FROM cases WHERE demandado LIKE '%AUGUSTO PAVANI%'")
    rad = c.fetchone()[0]
    print("Found Radicado Sqlite:", rad)

PORTLET_ID = "co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq"
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"
HEADERS = {"User-Agent": "Mozilla/5.0"}

async def test():
    params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        f"_{PORTLET_ID}_action": "busqueda",
        f"_{PORTLET_ID}_idDepto": rad[:2],
        f"_{PORTLET_ID}_idDespacho": rad[:12],
        f"_{PORTLET_ID}_fechaInicio": "01/01/2025",
        f"_{PORTLET_ID}_fechaFin": "31/12/2026",
    }
    
    async with httpx.AsyncClient(verify=False) as c:
        resp = await c.get(BASE_URL, params=params, headers=HEADERS)
        print("Status", resp.status_code)
        html = resp.text
        print("Contains AUGUSTO:", "AUGUSTO" in html.upper())
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr"):
            print("ROW:", tr.get_text(separator=' | ', strip=True)[:100])

if rad:
    asyncio.run(test())
