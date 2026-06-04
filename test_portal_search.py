import asyncio
import httpx
from bs4 import BeautifulSoup

PORTLET_ID = "co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq"
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

async def run_test(date_format):
    # Try with the specified date format
    if date_format == "dmy":
        fi = "01/04/2026"
        ff = "30/04/2026"
    else:
        fi = "2026-04-01"
        ff = "2026-04-30"

    params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        f"_{PORTLET_ID}_action": "busqueda",
        f"_{PORTLET_ID}_idDepto": "11",
        f"_{PORTLET_ID}_idDespacho": "110014003007",
        f"_{PORTLET_ID}_fechaInicio": fi,
        f"_{PORTLET_ID}_fechaFin": ff,
        f"_{PORTLET_ID}_verTotales": "true"
    }

    print(f"Testing with dates: {fi} to {ff}...")
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.get(BASE_URL, params=params, headers=HEADERS)
        print("Status Code:", resp.status_code)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for links or tables
        rows = soup.find_all("tr")
        print(f"Found {len(rows)} table rows.")
        
        # Let's inspect some content or links
        links = soup.find_all("a", href=True)
        print(f"Found {len(links)} links in total.")
        
        # Let's print unique links containing detail or detail.jsp
        detail_links = []
        for l in links:
            href = l["href"]
            if "detail" in href or "articleId" in href:
                detail_links.append((l.get_text(strip=True), href))
        
        print(f"Detail links found ({len(detail_links)}):")
        for text, href in detail_links[:10]:
            print(f"  - Text: {text} | URL: {href[:120]}...")

        # Also search for table structure
        for tr in rows[:10]:
            print("  Row content:", tr.get_text(separator=" | ", strip=True)[:150])

async def main():
    print("=== Format: YYYY-MM-DD ===")
    await run_test("ymd")
    print("\n=== Format: DD/MM/YYYY ===")
    await run_test("dmy")

if __name__ == "__main__":
    asyncio.run(main())
