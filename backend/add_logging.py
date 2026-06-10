import os

def print_errors():
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # replace "except Exception: conn.rollback()" with "except Exception as e: print(f'Auto-migration error: {e}'); conn.rollback()"
    new_content = content.replace(
        "except Exception: conn.rollback()",
        "except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}'); conn.rollback()"
    )
    
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    print_errors()
