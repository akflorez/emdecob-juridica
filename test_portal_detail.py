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
        
        # Find the row for Notificación por Estado No.041
        target_link = None
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if "Estado No.041" in text or "Estado No. 041" in text:
                target_link = a["href"]
                print(f"Found target link: {text} -> {target_link[:120]}...")
                break
        
        # If not found by name, try to find any link containing articleId that has "Ver detalle" next to the row for Estado 041
        # Let's inspect the HTML of the row
        if not target_link:
            print("Target link not found by exact text. Let's look through rows.")
            for tr in soup.find_all("tr"):
                txt = tr.get_text()
                if "041" in txt and "20 de abril de 2026" in txt:
                    # find link inside or near it
                    for a in tr.find_all("a", href=True):
                        if "detail" in a["href"] or "articleId" in a["href"]:
                            target_link = a["href"]
                            print(f"Found link in tr: {a.get_text(strip=True)} -> {target_link[:120]}...")
                            break
                    if target_link:
                        break

        if not target_link:
            print("Target link not found!")
            return

        # Request detail page
        print("Requesting detail page...")
        detail_resp = await client.get(target_link, headers=HEADERS)
        print("Detail status:", detail_resp.status_code)
        
        # Save HTML to check it
        with open("detail_041.html", "w", encoding="utf-8") as f:
            f.write(detail_resp.text)
        print("HTML saved to detail_041.html")
        
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
        
        # Let's print out all divs/sections/labels and their text to see the fields
        print("\n=== FIELD LABELS AND VALUES ===")
        for div in detail_soup.find_all("div"):
            # If div contains a label and a value or just text
            text = div.get_text(strip=True)
            if "Resumen de la" in text or "Cuadro" in text or "Providencia" in text or "Documentos de" in text:
                print(f"DIV [{div.get('class', '')}]: {text[:200]}...")

        # Let's find all links in the detail page and print them
        print("\n=== ALL LINKS IN DETAIL PAGE ===")
        for a in detail_soup.find_all("a", href=True):
            print(f"Link text: '{a.get_text(strip=True)}' | Href: {a['href']}")

if __name__ == "__main__":
    asyncio.run(main())
