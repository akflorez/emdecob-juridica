import asyncio
import httpx
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.getcwd())
from backend.service.publicaciones import build_portal_search_url, HEADERS

async def main():
    url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30")
    print(f"Fetching search page: {url}")
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for pagination elements or page numbers
        print("\n--- PAGINATION ELEMENTS ---")
        pagination = soup.find_all(class_=lambda x: x and ("pagination" in x or "page" in x or "nav" in x))
        for el in pagination[:10]:
            print(f"Tag: {el.name} | Class: {el.get('class')} | Text: {repr(el.get_text(strip=True)[:100])}")
            
        print("\n--- ALL LINKS WITH PAGES OR NUMBERS ---")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "page" in href.lower() or "page" in text.lower() or text.isdigit():
                print(f"Text: {repr(text)} | Href: {repr(href)}")

        # Search the raw html text for page indicators
        print("\n--- SEARCHING FOR TOTAL RECORDS OR PAGES ---")
        for phrase in ["total", "registro", "página", "pagina", "siguiente", "anterior", "next", "prev"]:
            count = resp.text.lower().count(phrase)
            print(f"Occurrences of '{phrase}': {count}")

if __name__ == "__main__":
    asyncio.run(main())
