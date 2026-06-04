import httpx
import sys
import os
sys.path.append(os.getcwd())
from backend.service.publicaciones import build_portal_search_url, HEADERS

async def main():
    search_url = build_portal_search_url("110014003007", "2025-06-01", "2025-06-30")
    detail_url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio?p_p_id=co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomMuni=BOGOT%C3%81+D.C.&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_jspPage=%2FMETA-INF%2Fresources%2Fdetail.jsp&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_articleId=118241031&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEspecialidad=CIVIL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDespacho=JUZGADO+007+CIVIL+MUNICIPAL+DE+BOGOT%C3%81&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEntidad=JUZGADO+MUNICIPAL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDepto=BOGOT%C3%81"
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        print("1. Performing search query to establish session...")
        s_resp = await client.get(search_url)
        print(f"   Search status: {s_resp.status_code}")
        
        print("2. Fetching detail page...")
        d_resp = await client.get(detail_url)
        print(f"   Detail status: {d_resp.status_code} | Length: {len(d_resp.text)}")
        
        with open("scratch/detail_056.html", "w", encoding="utf-8") as f:
            f.write(d_resp.text)
        print("Saved HTML to scratch/detail_056.html")

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
