from bs4 import BeautifulSoup

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    # Try finding elements with class "categoria-ep"
    elements = soup.find_all(class_="categoria-ep")
    print(f"Found {len(elements)} elements with class 'categoria-ep'")
    for el in elements:
        print(f"Element text: '{el.get_text(strip=True)}'")
        
    # Also find all elements inside div#metadata
    metadata_div = soup.find(id="metadata")
    if metadata_div:
        print("Metadata div content:")
        print(metadata_div.get_text(separator=" | ", strip=True))

if __name__ == "__main__":
    main()
