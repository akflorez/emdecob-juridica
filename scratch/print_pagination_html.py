import asyncio
import httpx
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.getcwd())
from backend.service.publicaciones import build_portal_search_url, HEADERS

async def main():
    url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30")
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        print("Searching for 'Anterior' or 'Siguiente'...")
        with open("scratch/pagination_html.txt", "w", encoding="utf-8") as f:
            for el in soup.find_all(string=True):
                if "siguiente" in el.lower() or "anterior" in el.lower():
                    parent = el.parent
                    f.write(f"Parent tag: {parent.name} | Class: {parent.get('class')}\n")
                    f.write(parent.prettify())
                    f.write("\n" + "=" * 40 + "\n")
        print("Saved pagination HTML to scratch/pagination_html.txt")

if __name__ == "__main__":
    asyncio.run(main())
