import sys
import os
sys.path.append(os.getcwd())
import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from backend.service.publicaciones import HEADERS, fitz, docx

async def extract_text_content_fixed(url: str, client: httpx.AsyncClient, timeout: int = 30) -> str:
    """Extrae texto de un PDF o DOCX remoto de forma asíncrona, resolviendo páginas intermedias de Liferay."""
    if not url: return ""
    try:
        # Si es un link de liferay intermedio, resolvemos el PDF real
        if "find_file_entry" in url or "SearchResultsPortlet" in url:
            print(f"[extractor] Resolviendo página intermedia: {url[:100]}...")
            resp = await client.get(url, timeout=timeout)
            if resp.status_code == 200:
                html = resp.text
                uuid_match = re.search(r'fileEntryUUID\s*:\s*["\']([^"\']+)["\']', html)
                group_match = re.search(r'groupId\s*:\s*["\']([^"\']+)["\']', html)
                if uuid_match and group_match:
                    uuid = uuid_match.group(1)
                    group_id = group_match.group(1)
                    url = f"https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/get_file?uuid={uuid}&groupId={group_id}"
                    print(f"[extractor] URL resuelta: {url}")
                else:
                    print("[extractor] No se encontró UUID/GroupID en la página intermedia")
        
        # Descargar el contenido
        resp = await client.get(url, timeout=timeout)
        if resp.status_code != 200: return ""
        
        content = resp.content
        text = ""
        
        # Intentar PDF
        if fitz:
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                for page in doc: text += page.get_text()
                doc.close()
                if text.strip(): return text
            except Exception as e:
                print("[extractor] Error al decodificar PDF:", e)
        
        # Intentar DOCX
        if docx:
            try:
                doc_io = docx.Document(io.BytesIO(content))
                text = "\n".join([p.text for p in doc_io.paragraphs])
                if text.strip(): return text
            except Exception as e:
                print("[extractor] Error al decodificar DOCX:", e)
            
        soup = BeautifulSoup(content, "html.parser")
        return soup.get_text()
    except Exception as e:
        print(f"[extractor] Error general {url[:50]}: {e}")
        return ""

async def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/find_file_entry?p_l_id=8843926&noSuchEntryRedirect=https%3A%2F%2Fpublicacionesprocesales.ramajudicial.gov.co%2Fweb%2Fpublicaciones-procesales%2Fsearch%3Fp_p_id%3Dcom_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ%26p_p_lifecycle%3D0%26p_p_state%3Dmaximized%26p_p_mode%3Dview%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_mvcPath%3D%252Fview_content.jsp%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_redirect%3D%252Fweb%252Fpublicaciones-procesales%252Fsearch%253Fq%253D110014003024%252B2024-01403%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_assetEntryId%3D88129408%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_type%3Ddocument&fileEntryId=88129406&inheritRedirect=true"
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        text = await extract_text_content_fixed(url, client)
        print("\nExtracted text length:", len(text))
        print("First 300 chars of extracted text:")
        print(repr(text[:300]))

if __name__ == '__main__':
    asyncio.run(main())
