import sys

filename = r"c:\Users\ANA KARINA\Desktop\emdecob consultas\backend\main.py"

with open(filename, 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')

for i, line in enumerate(content.splitlines()):
    for char in line:
        if ord(char) > 127:
            print(f"Line {i+1}: Found non-ASCII character {char} (ord {ord(char)})")
            break
