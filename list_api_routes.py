import re
with open('backend/main.py', encoding='utf-8') as f:
    content = f.read()

routes = re.findall(r'@app\.\w+\("(/api/[^"]+)"', content)
print('\n'.join(sorted(set(routes))))
