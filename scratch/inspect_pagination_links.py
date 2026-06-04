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
        
        print("\n--- pagination ul HTML ---")
        pagination_ul = soup.find("ul", class_="pagination")
        if pagination_ul:
            print(pagination_ul.prettify())
            for a in pagination_ul.find_all("a", href=True):
                print(f"Text: {repr(a.get_text(strip=True))} | Href: {repr(a['href'])}")
        else:
            print("No pagination ul found")

if __name__ == "__main__":
    asyncio.run(main())
