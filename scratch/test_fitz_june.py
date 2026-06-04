import asyncio
import httpx
import fitz

async def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/get_file?uuid=26e38206-8d8a-530e-5431-fe69cf5b9991&groupId=6098902"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    print("Downloading PDF...")
    async with httpx.AsyncClient(headers=headers, verify=False, timeout=60) as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code} | Bytes: {len(resp.content)}")
        
        try:
            doc = fitz.open(stream=resp.content, filetype="pdf")
            print(f"Pages: {len(doc)}")
            for i, page in enumerate(doc):
                text = page.get_text()
                print(f"Page {i+1} text length: {len(text)}")
                images = page.get_images()
                print(f"Page {i+1} images count: {len(images)}")
                if len(text) > 0:
                    print(f"Text snippet: {repr(text[:300])}")
            doc.close()
        except Exception as e:
            print(f"Error opening with fitz: {e}")

if __name__ == "__main__":
    asyncio.run(main())
