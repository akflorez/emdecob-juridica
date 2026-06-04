from bs4 import BeautifulSoup

def main():
    with open("scratch/detail_056.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    print("--- ALL LINKS CONTAINING ATTACHMENTS ---")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if "get_file" in href or "documents" in href or "detail" in href or "article" in href:
            print(f"Text: {repr(text)} | Href: {repr(href)}")
            
    print("\n--- ALL DATOS TITLE/DESCRIPTION BLOCKS ---")
    for div in soup.find_all("div", class_="datos"):
        title = div.find("div", class_="datosTitle")
        desc = div.find("div", class_="datosDescription")
        title_text = title.get_text(strip=True) if title else "No Title"
        desc_text = desc.get_text(strip=True) if desc else "No Desc"
        print(f"Title: {repr(title_text)} | Description: {repr(desc_text)}")
        for a in div.find_all("a", href=True):
            print(f"  Link inside div: Text={repr(a.get_text(strip=True))} Href={repr(a['href'])}")

if __name__ == "__main__":
    main()
