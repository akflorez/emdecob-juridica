import asyncio
import httpx
from backend.service.publicaciones import extract_text_content, find_radicado_in_context, normalize_text

async def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/c/document_library/get_file?uuid=3322438a-7425-26c3-c8f8-b1c85067efb4&groupId=6098902"
    radicado = "11001400300720250052200"
    
    print("Downloading...")
    async with httpx.AsyncClient(verify=False, timeout=60) as client:
        text = await extract_text_content(url, client)
        
    print(f"Extracted text length: {len(text)} characters")
    if text:
        # Print lines around "522"
        print("\nSurrounding lines around '522':")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if "522" in line:
                start_i = max(0, idx - 10)
                end_i = min(len(lines), idx + 10)
                print(f"--- Context block for line {idx} ---")
                for i in range(start_i, end_i):
                    marker = ">>>" if i == idx else "   "
                    print(f"{marker} Line {i:03d}: {lines[i]}")
                print("-" * 30)
        print("First 500 characters of text:")
        print(text[:500])
        print("\nChecking match:")
        match = find_radicado_in_context(text, radicado)
        print(f"Match is_valid: {match.is_valid}")
        print(f"Match type: {match.match_type}")
        print(f"Match reasons: {match.reasons}")
        
        # Check if the internal number "00522" or "2025-00522" is in the text
        print(f"\nIs '00522' in text: {'00522' in text}")
        print(f"Is '2025' in text: {'2025' in text}")
        
        # Print lines containing "522"
        print("\nLines with '522':")
        for line in text.splitlines():
            if "522" in line:
                print(line)

if __name__ == "__main__":
    asyncio.run(main())
