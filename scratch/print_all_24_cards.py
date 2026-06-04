import httpx
from backend.service.publicaciones import build_portal_search_url, HEADERS, parse_result_cards

async def main():
    url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30") + "&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_delta=75"
    print(f"URL: {url}")
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(url)
        cards = parse_result_cards(resp.text)
        print(f"Total cards returned: {len(cards)}")
        
        for idx, card in enumerate(cards):
            print(f"Card #{idx+1:02d}: Title={repr(card['title'])} | Date={repr(card['fecha_publicacion'])} | ArticleId={repr(card['detail_url'].split('articleId=')[-1].split('&')[0])}")

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
