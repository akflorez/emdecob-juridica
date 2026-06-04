def main():
    with open("detail_041.html", "r", encoding="utf-8") as f:
        html = f.read()

    print("Found 'JUZGADO 003' in raw HTML:", "JUZGADO 003" in html)
    print("Found 'QUIND' in raw HTML:", "QUIND" in html.upper())
    print("Found 'ARMENIA' in raw HTML:", "ARMENIA" in html.upper())

if __name__ == "__main__":
    main()
