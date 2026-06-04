import asyncio
import httpx
from bs4 import BeautifulSoup

PORTLET_ID = "co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq"
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

async def main():
    params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        f"_{PORTLET_ID}_action": "busqueda",
        f"_{PORTLET_ID}_idDepto": "63",
        f"_{PORTLET_ID}_idDespacho": "630013110003",
        f"_{PORTLET_ID}_fechaInicio": "2026-04-01",
        f"_{PORTLET_ID}_fechaFin": "2026-04-30",
        f"_{PORTLET_ID}_verTotales": "true"
    }

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.get(BASE_URL, params=params, headers=HEADERS)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        rows = soup.find_all("tr")
        print(f"Total rows: {len(rows)}")
        
        # Look for the table
        # Let's inspect rows that have table headers or table cells
        for i, tr in enumerate(rows[:5]):
            print(f"\n--- Row #{i} ---")
            # print tr's HTML
            print(tr.prettify()[:1000])

if __name__ == "__main__":
    asyncio.run(main())
