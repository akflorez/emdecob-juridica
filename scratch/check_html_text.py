import httpx
from bs4 import BeautifulSoup

def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio?p_p_id=co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomMuni=BOGOT%C3%81+D.C.&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_jspPage=%2FMETA-INF%2Fresources%2Fdetail.jsp&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_articleId=118241031&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEspecialidad=CIVIL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDespacho=JUZGADO+007+CIVIL+MUNICIPAL+DE+BOGOT%C3%81&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomEntidad=JUZGADO+MUNICIPAL&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortletV2_INSTANCE_BIyXQFHVaYaq_nomDepto=BOGOT%C3%81"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    resp = httpx.get(url, headers=headers, verify=False, timeout=60)
    print(f"Status: {resp.status_code}")
    soup = BeautifulSoup(resp.text, 'html.parser')
    body_text = soup.body.get_text() if soup.body else 'No body'
    
    # Print search results for key strings
    for keyword in ["No encontrado", "error", "ESTADO", "056", "documento", "archivo"]:
        count = body_text.lower().count(keyword.lower())
        print(f"Count of '{keyword}': {count}")
        
    print("\n--- SNIPPET ---")
    snippet = " ".join(body_text.split())[:1500]
    print(snippet.encode('ascii', errors='replace').decode('ascii'))

if __name__ == "__main__":
    main()
