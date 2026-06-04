from bs4 import BeautifulSoup

def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    for div in soup.find_all("div", class_="datos"):
        title_div = div.find("div", class_="datosTitle")
        desc_div = div.find("div", class_="datosDescription")
        if title_div and desc_div:
            title = title_div.get_text(strip=True)
            value = desc_div.get_text(strip=True)
            print(f"Field: '{title}' => '{value}'")

if __name__ == "__main__":
    main()
