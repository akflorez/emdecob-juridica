import requests

try:
    print("Testing GET https://consultasjuridicas.emdecob.com/api/stats ...")
    resp = requests.get("https://consultasjuridicas.emdecob.com/api/stats")
    print(f"Status Code: {resp.status_code}")
    print(f"Response Body (100 chars): {resp.text[:100]}")
    
    print("\nTesting GET https://consultasjuridicas.emdecob.com/api/bulk-sync/publications-status ...")
    resp2 = requests.get("https://consultasjuridicas.emdecob.com/api/bulk-sync/publications-status")
    print(f"Status Code: {resp2.status_code}")
    print(f"Response Body (100 chars): {resp2.text[:100]}")

except Exception as e:
    print(f"Error: {e}")
