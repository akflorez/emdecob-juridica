import urllib.request
import json
import urllib.error

data = json.dumps({'username': 'akflorez', 'password': 'Emdecob2026*'}).encode()
req = urllib.request.Request('http://84.247.130.122:8090/api/auth/login', data=data, headers={'Content-Type': 'application/json'})

try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(e.headers)
    print(e.read().decode())
