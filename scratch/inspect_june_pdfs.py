import httpx
import fitz
import io

async def inspect_pdf(url, name):
    print(f"\n--- INSPECTING {name} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, verify=False, timeout=60) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"Error downloading {name}: HTTP {resp.status_code}")
            return
        
        content = resp.content
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        print(f"Text length: {len(text)}")
        # Search for consecutivo
        for term in ["00522", "522", "TALERO", "FONDO NACIONAL"]:
            count = text.lower().count(term.lower())
            print(f"Occurrences of '{term}': {count}")
            
        # Print lines containing any match
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "522" in line or "TALERO" in line or "00522" in line:
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                print(f"Context around line {i}:")
                for j in range(start, end):
                    print(f"  {j}: {lines[j]}")
                print("-" * 15)

import asyncio
async def main():
    pdf1 = "https://publicacionesprocesales.ramajudicial.gov.co/documents/6098902/118210133/Estado+056-25.pdf/26e38206-8d8a-530e-5431-fe69cf5b9991?t=1749071060000"
    pdf2 = "https://publicacionesprocesales.ramajudicial.gov.co/documents/6098902/118210133/Estado+055.pdf/405a767e-2cf8-8ca0-ab1b-262174300000?t=1749046399000"
    await inspect_pdf(pdf1, "Estado 056-25.pdf")
    await inspect_pdf(pdf2, "Estado 055.pdf")

if __name__ == "__main__":
    asyncio.run(main())
