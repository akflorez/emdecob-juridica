from bs4 import BeautifulSoup

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
        
    # Search for visible text lines containing QUIND, ARMENIA, FAMILIA, JUZGADO
    for text in soup.stripped_strings:
        if any(k in text.lower() for k in ["quind", "armenia", "familia", "juzgado"]):
            print(f"Visible Text: {repr(text)}")

if __name__ == "__main__":
    main()
