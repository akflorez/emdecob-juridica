import sys
import os
sys.path.append(os.getcwd())
import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from backend.service.publicaciones import HEADERS

async def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search"
    params = {"q": "110014003024 2024-01403"}
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Find all search result links
            links = [l for l in soup.find_all("a", href=True) if "find_file_entry" in l["href"] or "/documents/" in l["href"]]
            print("Links found in search:", len(links))
            
            # Let's inspect the first entry HTML to see what parameters it has
            if links:
                first_link = links[0]
                print("\n--- First Link ---")
                print(str(first_link))
                print("\nParent:", str(first_link.parent))
                print("\nParent's parent:", str(first_link.parent.parent)[:1000])
                
                # Check if there is any data-* attributes, metadata, or scripts
                print("\nAttributes of first entry:", first_entry.attrs)
                
                # Let's search if the search page contains a JSON or JavaScript object with all entries
                # like Liferay.Portlet or window.Analytics or similar
                scripts = soup.find_all("script")
                print(f"\nTotal scripts on search page: {len(scripts)}")
                for i, s in enumerate(scripts):
                    text = s.string or ""
                    if "documentPreviewed" in text or "fileEntryId" in text:
                        print(f"Script #{i} contains documentPreviewed/fileEntryId! Length: {len(text)}")
                        # Print occurrences
                        for m in re.finditer(r'\{fileEntryId:[^}]+\}', text):
                            print("Found entry config:", m.group(0))

if __name__ == '__main__':
    asyncio.run(main())
