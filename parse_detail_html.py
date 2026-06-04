import re
from bs4 import BeautifulSoup

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    out = []
    
    # Let's find labels and values.
    # In Liferay pages, details are often presented in groups or lists of divs, or tables.
    # Let's inspect divs that look like fields
    out.append("=== Liferay details ===")
    for label_elem in soup.find_all(text=True):
        parent = label_elem.parent
        # Look for labels like "Resumen de la", "Cuadro", "Providencia", "Documentos", "Fecha", "Estado"
        txt = label_elem.strip()
        if not txt: continue
        if any(k in txt.lower() for k in ["resumen", "cuadro", "providencia", "documento", "fecha", "estado"]):
            # print parent hierarchy or contents
            out.append(f"Found text: {txt} | Parent Tag: {parent.name} | Class: {parent.get('class', '')}")
            # print sibling text or parent's text
            out.append(f"  Parent full text: {parent.get_text(separator=' | ', strip=True)[:300]}")

    out.append("\n=== All links in the page ===")
    for a in soup.find_all("a", href=True):
        out.append(f"Text: '{a.get_text(strip=True)}' | Href: {a['href']}")

    with open("parsed_detail_info.txt", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(out))
        
    print("Parsed output saved to parsed_detail_info.txt")

if __name__ == "__main__":
    main()
