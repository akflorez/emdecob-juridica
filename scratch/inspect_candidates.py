import sys
import os
sys.path.append(os.getcwd())
import asyncio
import httpx
from bs4 import BeautifulSoup
from backend.service.publicaciones import get_candidates, extract_text_content, HEADERS, normalize_text

async def main():
    rad_digits = "11001400302420240140300"
    url = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/search"
    params = {"q": "110014003024 2024-01403"}
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        resp = await client.get(url, params=params)
        print("Status code:", resp.status_code)
        if resp.status_code == 200:
            candidates = await get_candidates(resp.text, rad_digits)
            print("Candidates found:", len(candidates))
            for i, cand in enumerate(candidates):
                print(f"\n--- Candidate #{i+1} ---")
                print("URL:", cand["documento_url"])
                print("Is Direct:", cand["is_direct"])
                print("Snippet:", cand["snippet"])
                
                # Fetch content
                doc_text = ""
                if not cand["is_direct"]:
                    inner_resp = await client.get(cand["documento_url"])
                    if inner_resp.status_code == 200:
                        inner_soup = BeautifulSoup(inner_resp.text, "html.parser")
                        inner_links = inner_soup.find_all("a", href=True)
                        for il in inner_links:
                            link_text = il.get_text().upper()
                            href = il["href"]
                            if any(k in link_text for k in ["VER", "CONSULTAR", "AQUI", "DETALLE"]) or ".pdf" in href.lower():
                                if not href.startswith("http"):
                                    href = "https://publicacionesprocesales.ramajudicial.gov.co" + (href if href.startswith("/") else "/" + href)
                                print("Navigating inner link:", href)
                                doc_text = await extract_text_content(href, client)
                                break
                else:
                    doc_text = await extract_text_content(cand["documento_url"], client)
                
                print("Extracted text length:", len(doc_text))
                if doc_text:
                    print("Extracted text sample (first 400 chars):")
                    print(repr(doc_text[:400]))
                    t_norm = "".join(normalize_text(doc_text).split())
                    print("Contains 23-digit radicado ('11001400302420240140300'):", "11001400302420240140300" in t_norm)
                    print("Contains pattern ('202401403'):", "202401403" in t_norm)
                    # check demandante parts
                    dante = "FONDO NACIONAL DEL AHORRO CARLOS LLERAS RESTREPO"
                    dado = "PEDRO ELIAS MORENO GONZALES"
                    n_dante = dante.upper().replace("S.A.S.", "").replace("SAS", "").replace("S.A.", "").replace("LIMITADA", "").replace("LTDA", "").replace("E.S.P.", "").replace("ESP", "")
                    words_dante = [w.lower() for w in n_dante.split() if len(w) > 3 and w not in ["BANCO", "SISTEMA", "GESTION", "COBRANZAS", "MUNICIPIO", "PARA", "LAS", "LOS", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA"]]
                    n_dado = dado.upper().replace("S.A.S.", "").replace("SAS", "").replace("S.A.", "").replace("LIMITADA", "").replace("LTDA", "").replace("E.S.P.", "").replace("ESP", "")
                    words_dado = [w.lower() for w in n_dado.split() if len(w) > 3 and w not in ["BANCO", "SISTEMA", "GESTION", "COBRANZAS", "MUNICIPIO", "PARA", "LAS", "LOS", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA"]]
                    
                    matched_dante = [w for w in words_dante if w in t_norm]
                    matched_dado = [w for w in words_dado if w in t_norm]
                    print("Demandante words:", words_dante, "Matched:", matched_dante)
                    print("Demandado words:", words_dado, "Matched:", matched_dado)

if __name__ == '__main__':
    asyncio.run(main())
