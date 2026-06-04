from bs4 import BeautifulSoup

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    for b in soup.find_all("b"):
        txt = b.get_text(strip=True)
        if any(k in txt.lower() for k in ["estado no", "fecha de publica", "fecha de estado"]):
            print(f"B text: {txt}")
            parent = b.parent
            print(f"  Parent: {parent.name} | Class: {parent.get('class', '')} | Content: {parent}")
            # Let's print the parent's siblings
            siblings = list(parent.next_siblings)
            for i, sib in enumerate(siblings[:3]):
                if sib.name:
                    print(f"  Sibling {i}: <{sib.name} class='{sib.get('class', '')}'>: {sib.get_text(strip=True)}")
                else:
                    print(f"  Sibling {i} (text): {repr(sib)}")
            # Let's print the parent's parent contents to be sure
            gp = parent.parent
            print(f"  Grandparent: {gp.name} | class: {gp.get('class', '')}")
            # print first 500 chars of grandparent HTML
            print(f"  Grandparent HTML snippet:\n{gp.prettify()[:600]}")
            print("-" * 50)
            
if __name__ == "__main__":
    main()
