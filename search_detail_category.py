from bs4 import BeautifulSoup
import re

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
        
    for text in soup.find_all(text=True):
        txt = text.strip()
        if any(k in txt.lower() for k in ["categor", "tipo de"]):
            print(f"Parent: {text.parent.name} | Text: {repr(txt)}")

if __name__ == "__main__":
    main()
