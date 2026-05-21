import re
with open('scratch/entry.html', encoding='utf-8') as f:
    html = f.read()

uuid_match = re.search(r'fileEntryUUID\s*:\s*["\']([^"\']+)["\']', html)
group_match = re.search(r'groupId\s*:\s*["\']([^"\']+)["\']', html)

print('UUID:', uuid_match.group(1) if uuid_match else None)
print('GroupID:', group_match.group(1) if group_match else None)
