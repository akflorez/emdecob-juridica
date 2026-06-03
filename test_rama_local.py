import httpx
import time
import json

def test_rama_connection():
    url = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2/Procesos/Consulta/NumeroRadicado?numero=11001400306720250052600&SoloActivos=false"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://consultaprocesos.ramajudicial.gov.co",
        "Referer": "https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicado"
    }

    start = time.time()
    try:
        with httpx.Client(verify=False, timeout=15.0) as client:
            resp = client.get(url, headers=headers)
        
        elapsed = time.time() - start
        
        result = {
            "environment": "Local",
            "url": url,
            "status_code": resp.status_code,
            "response_time_ms": round(elapsed * 1000, 2),
            "response_headers": dict(resp.headers),
            "response_preview": resp.text[:200] + "..." if len(resp.text) > 200 else resp.text,
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start
        result = {
            "environment": "Local",
            "url": url,
            "status_code": None,
            "response_time_ms": round(elapsed * 1000, 2),
            "response_headers": None,
            "response_preview": None,
            "error": str(e)
        }
        
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_rama_connection()
