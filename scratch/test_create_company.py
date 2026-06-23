import urllib.request
import json

token = "gAAAAABqIcG_h9hLQ17Y_p1KKRdQP0udPJpnNUTpN9kvNcCpk_cWEKV893_Eef3-8klfn7jXl2fLe73rqsmNSfKYASczuPTl8A=="
url = "http://84.247.130.122:8090/api/admin/companies"

data = {
    "nombre": "emdecob test",
    "nit": "900000000",
    "limite_usuarios": 5
}
payload = json.dumps(data).encode('utf-8')

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

print(f"POSTing to {url}...")
req = urllib.request.Request(url, data=payload, method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("User-Agent", user_agent)
req.add_header("Content-Type", "application/json")

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        status = response.getcode()
        body = response.read().decode('utf-8')
        print(f"STATUS: {status}")
        print(f"BODY: {body}")
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR: {e.code}")
    try:
        print(f"BODY: {e.read().decode('utf-8')}")
    except Exception:
        print("Could not read body")
except Exception as e:
    print(f"ERROR: {e}")
