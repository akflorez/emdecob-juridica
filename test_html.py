import asyncio
import httpx

PORTLET_ID = "co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq"
BASE_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio"
HEADERS = {"User-Agent": "Mozilla/5.0"}

async def test():
    params = {
        "p_p_id": PORTLET_ID,
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        f"_{PORTLET_ID}_action": "busqueda",
        f"_{PORTLET_ID}_idDepto": "11",
        f"_{PORTLET_ID}_idDespacho": "110014003033", # JUZGADO 033 CIVIL DEL CIRCUITO DE BOGOTÁ ( Wait, 033 CCTO is usually 110013103033! )
        f"_{PORTLET_ID}_fechaInicio": "01/01/2025",
        f"_{PORTLET_ID}_fechaFin": "31/12/2026",
    }
    # Wait, the radicado might be 110014003033... Wait, the screenshot says "JUZGADO 033 CIVIL DEL CIRCUITO DE BOGOTA"
    from backend.db import SessionLocal
    from backend.models import Case
    import json
    db = SessionLocal()
    case = db.query(Case).filter(Case.demandado.like("%AUGUSTO PAVANI%")).first()
    if case:
        print("Caso encontrado:", case.radicado)
        acts = json.loads(case.actuaciones_json or "[]")
        if acts: print("KEYS:", acts[0].keys())
        return
        rad = case.radicado
        print(f"Radicado: {rad}")
        params[f"_{PORTLET_ID}_idDepto"] = rad[:2]
        params[f"_{PORTLET_ID}_idDespacho"] = rad[:12]
    
    async with httpx.AsyncClient(verify=False) as c:
        resp = await c.get(BASE_URL, params=params, headers=HEADERS)
        print("Status", resp.status_code)
        html = resp.text
        print("Result length:", len(html))
        print("Contains AUGUSTO:", "AUGUSTO" in html.upper())
        print("Contains PAVANI:", "PAVANI" in html.upper())
        # Print table snippets
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr"):
            print("ROW:", tr.get_text(separator=' | ', strip=True)[:100])

import sys, os
sys.path.append(os.getcwd())
asyncio.run(test())
