import urllib.request
import json

token = "gAAAAABqIcG_h9hLQ17Y_p1KKRdQP0udPJpnNUTpN9kvNcCpk_cWEKV893_Eef3-8klfn7jXl2fLe73rqsmNSfKYASczuPTl8A=="

urls = [
    "https://consultasjuridicas.emdecob.com/api/auth/me",
    "https://consultasjuridicas.emdecob.com/api/admin/companies",
    "https://consultasjuridicas.emdecob.com/api/admin/users",
    "https://consultasjuridicas.emdecob.com/api/admin/billing/tiers",
    "https://consultasjuridicas.emdecob.com/api/admin/billing/simulator"
]

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

for url in urls:
    print(f"\nRequesting {url}...")
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", user_agent)
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"STATUS: {status}")
            print(f"BODY: {body}")
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR: {e.code}")
        print(f"BODY: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"ERROR: {e}")
