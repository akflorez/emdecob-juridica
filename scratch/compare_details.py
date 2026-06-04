import sys
import os
sys.path.append(os.getcwd())
import httpx
from backend.service.publicaciones import build_portal_search_url, HEADERS

async def fetch_and_save(article_id, filename):
    url = f"https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio?p_p_id=co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomMuni=BOGOT%C3%81+D.C.&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_jspPage=%2FMETA-INF%2Fresources%2Fdetail.jsp&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_articleId={article_id}&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEspecialidad=CIVIL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDespacho=JUZGADO+007+CIVIL+MUNICIPAL+DE+BOGOT%C3%81&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEntidad=JUZGADO+MUNICIPAL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDepto=BOGOT%C3%81"
    
    search_url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30")
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        # Establish session
        await client.get(search_url)
        # Get detail
        resp = await client.get(url)
        print(f"Article {article_id}: Status {resp.status_code} | Length {len(resp.text)}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(resp.text)

import asyncio
async def main():
    await fetch_and_save("121650729", "scratch/detail_032.html")
    await fetch_and_save("118241031", "scratch/detail_056.html")

if __name__ == "__main__":
    asyncio.run(main())
