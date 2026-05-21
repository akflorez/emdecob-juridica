import sys
import os
sys.path.append(os.getcwd())
import asyncio
import httpx
from backend.service.publicaciones import HEADERS, fitz

async def main():
    # Construct Liferay direct download URL using UUID and GroupID
    uuid = "2cdd68c5-eb94-ba42-bdbc-cf1f6ad87cf9"
    groupId = "6098902"
    url = f"https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/get_file?uuid={uuid}&groupId={groupId}"
    
    # Or try folderId/title/fileEntryId/groupId style if uuid fails
    # url = f"https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/get_file?p_l_id=8843926&folderId=0&title=2024+01403+AutoRequiereArt317.pdf&fileEntryId=88129406&groupId=6098902"
    
    print("Testing URL:", url)
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(url)
        print("Status code:", resp.status_code)
        print("Content type:", resp.headers.get("content-type"))
        print("Content length:", len(resp.content))
        
        if resp.status_code == 200 and "pdf" in resp.headers.get("content-type", "").lower():
            print("Successfully downloaded PDF!")
            if fitz:
                try:
                    doc = fitz.open(stream=resp.content, filetype="pdf")
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    print("Extracted text successfully! Total length:", len(text))
                    print("Sample:\n", text[:300])
                except Exception as e:
                    print("Error parsing PDF with PyMuPDF:", e)

if __name__ == '__main__':
    asyncio.run(main())
