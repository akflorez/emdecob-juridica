import sys
import os
sys.path.append(os.getcwd())
import asyncio
import httpx
from backend.service.publicaciones import HEADERS, extract_text_content, validate_content, normalize_text

async def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/find_file_entry?p_l_id=8843926&noSuchEntryRedirect=https%3A%2F%2Fpublicacionesprocesales.ramajudicial.gov.co%2Fweb%2Fpublicaciones-procesales%2Fsearch%3Fp_p_id%3Dcom_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ%26p_p_lifecycle%3D0%26p_p_state%3Dmaximized%26p_p_mode%3Dview%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_mvcPath%3D%252Fview_content.jsp%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_redirect%3D%252Fweb%252Fpublicaciones-procesales%252Fsearch%253Fq%253D110014003024%252B2024-01403%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_assetEntryId%3D98113972%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_type%3Ddocument&fileEntryId=98113970&inheritRedirect=true"
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        text = await extract_text_content(url, client)
        print("Text Length:", len(text))
        print("Text content:")
        print(text)
        
        # Test validate_content
        demandante = 'FONDO NACIONAL DEL AHORRO CARLOS LLERAS RESTREPO'
        demandado = 'PEDRO ELIAS MORENO GONZALES'
        
        t_norm = "".join(normalize_text(text).split())
        
        # Let's inspect significant_words
        def significant_words(name):
            if not name: return []
            n = name.upper().replace("S.A.S.", "").replace("SAS", "").replace("S.A.", "").replace("LIMITADA", "").replace("LTDA", "").replace("E.S.P.", "").replace("ESP", "")
            return [w.lower() for w in n.split() if len(w) > 3 and w not in ["BANCO", "SISTEMA", "GESTION", "COBRANZAS", "MUNICIPIO", "PARA", "LAS", "LOS", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA"]]
            
        words_dante = significant_words(demandante)
        words_dado = significant_words(demandado)
        
        print("Dante words:", words_dante)
        for w in words_dante:
            print(f"Is '{w}' in t_norm? {w in t_norm}")
            
        print("Dado words:", words_dado)
        for w in words_dado:
            print(f"Is '{w}' in t_norm? {w in t_norm}")

if __name__ == '__main__':
    asyncio.run(main())
