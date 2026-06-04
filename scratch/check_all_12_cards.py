import httpx
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.getcwd())
from backend.service.publicaciones import build_portal_search_url, HEADERS, parse_result_cards

async def main():
    search_url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30")
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        s_resp = await client.get(search_url)
        cards = parse_result_cards(s_resp.text)
        print(f"Total cards parsed: {len(cards)}")
        
        for idx, card in enumerate(cards):
            print(f"Card #{idx+1}: Title={repr(card['title'])} | Date={repr(card['fecha_publicacion'])}")

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
