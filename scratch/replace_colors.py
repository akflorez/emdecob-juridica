import os

def replace_colors():
    css_path = "frontend/src/index.css"
    if not os.path.exists(css_path):
        print(f"{css_path} not found")
        return
        
    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace primary color (174 83% 36%) with green (158 100% 36%)
    new_content = content.replace("174 83% 36%", "158 100% 36%")
    
    # Replace lighter accent color (174 60% 45%) with green accent (158 75% 45%)
    new_content = new_content.replace("174 60% 45%", "158 75% 45%")
    
    # Update gradient to go from JURICOB green to teal
    new_content = new_content.replace(
        "linear-gradient(135deg, hsl(174 83% 36%), hsl(199 89% 48%))",
        "linear-gradient(135deg, hsl(158 100% 36%), hsl(174 83% 36%))"
    )
    
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully replaced corporate theme colors in index.css")

if __name__ == "__main__":
    replace_colors()
