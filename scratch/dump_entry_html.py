import sys
import os
sys.path.append(os.getcwd())
import asyncio
import httpx
from backend.service.publicaciones import HEADERS

async def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/find_file_entry?p_l_id=8843926&noSuchEntryRedirect=https%3A%2F%2Fpublicacionesprocesales.ramajudicial.gov.co%2Fweb%2Fpublicaciones-procesales%2Fsearch%3Fp_p_id%3Dcom_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ%26p_p_lifecycle%3D0%26p_p_state%3Dmaximized%26p_p_mode%3Dview%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_mvcPath%3D%252Fview_content.jsp%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_redirect%3D%252Fweb%252Fpublicaciones-procesales%252Fsearch%253Fq%253D110014003024%252B2024-01403%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_assetEntryId%3D88129408%26_com_liferay_portal_search_web_search_results_portlet_SearchResultsPortlet_INSTANCE_PqxijW3cplDJ_type%3Ddocument&fileEntryId=88129406&inheritRedirect=true"
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(url)
        print("Status code:", resp.status_code)
        print("Final URL:", resp.url)
        with open("scratch/entry.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("Saved to scratch/entry.html")

if __name__ == '__main__':
    asyncio.run(main())
