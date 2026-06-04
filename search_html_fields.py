from bs4 import BeautifulSoup
import re

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    # Search for QUINDIO
    results = soup.find_all(text=re.compile("QUIND", re.IGNORECASE))
    print(f"Matches for 'QUIND': {len(results)}")
    for r in results[:10]:
        print(f"Tag: {r.parent.name} | Class: {r.parent.get('class')} | Text: {r.strip()}")
        print(f"Parent HTML: {r.parent.prettify()[:200]}")
        print("-" * 30)

if __name__ == "__main__":
    main()
