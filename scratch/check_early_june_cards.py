import httpx
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.getcwd())
from backend.service.publicaciones import build_portal_search_url, HEADERS, parse_result_cards, detect_main_sources

async def main():
    search_url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30")
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        print("1. Performing search query...")
        s_resp = await client.get(search_url)
        cards = parse_result_cards(s_resp.text)
        print(f"Total cards parsed: {len(cards)}")
        
        # We only care about cards 1 to 5
        for idx in range(min(5, len(cards))):
            card = cards[idx]
            print(f"\n--- Card #{idx+1} ---")
            print(f"Title: {card['title']}")
            print(f"Date: {card['fecha_publicacion']}")
            print(f"Detail URL: {card['detail_url']}")
            
            # Fetch detail
            d_resp = await client.get(card['detail_url'])
            soup = BeautifulSoup(d_resp.text, "html.parser")
            sources = detect_main_sources(d_resp.text)
            print(f"Detail status: {d_resp.status_code} | Length: {len(d_resp.text)}")
            print(f"Sources: {sources}")
            
            # Print body text word count for "Estado"
            body_text = soup.body.get_text() if soup.body else ""
            print(f"Occurrences of 'Estado': {body_text.lower().count('estado')}")
            # Show any a tags inside the portlet
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "get_file" in href or "documents" in href:
                    if "infografia" not in href and "ABC" not in href:
                        links.append((a.get_text(strip=True), href))
            print(f"Specific links: {links}")

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
