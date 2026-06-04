import re
from bs4 import BeautifulSoup

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Locate "Resumen de la publicación"
    resumen_header = None
    for h4 in soup.find_all("h4"):
        if "resumen de la publicación" in h4.get_text().lower():
            resumen_header = h4
            break
            
    if resumen_header:
        print("=== RESUMEN DE LA PUBLICACION SECTION ===")
        # Get its parent or immediate siblings
        sibling = resumen_header.find_next_sibling()
        if sibling:
            print("Sibling tag:", sibling.name, "Class:", sibling.get("class", ""))
            print(sibling.prettify()[:1000])
        else:
            print("No sibling found. Parent:")
            print(resumen_header.parent.prettify()[:1000])
            
    # Locate "Documentos de la publicación"
    docs_header = None
    for h4 in soup.find_all("h4"):
        if "documentos de la publicación" in h4.get_text().lower():
            docs_header = h4
            break
            
    if docs_header:
        print("\n=== DOCUMENTOS DE LA PUBLICACION SECTION ===")
        print(docs_header.parent.prettify()[:1000])

if __name__ == "__main__":
    main()
