with open("backend/main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_context(line_num):
    print(f"\n--- Context for line {line_num} ---")
    start = max(0, line_num - 15)
    end = min(len(lines), line_num + 10)
    for idx in range(start, end):
        print(f"{idx+1}: {lines[idx]}", end="")

search_lines = [5016, 7126, 7156, 7185, 7197, 7230, 7256, 7281]
for l in search_lines:
    print_context(l)
