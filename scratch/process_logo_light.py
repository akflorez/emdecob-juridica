import os
from PIL import Image

def process_logo_light():
    logo_path = "logo juricob para modo claro.png"
    if not os.path.exists(logo_path):
        print(f"{logo_path} not found")
        return
        
    img = Image.open(logo_path).convert("RGBA")
    width, height = img.size
    print(f"Light logo loaded: {width}x{height}")
    
    # Convert white background to transparent (R > 245, G > 245, B > 245)
    datas = img.getdata()
    new_data = []
    
    for item in datas:
        if item[0] > 245 and item[1] > 245 and item[2] > 245:
            new_data.append((255, 255, 255, 0)) # Fully transparent
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    # We use the same bounding box as the dark shield logo.
    # Overall bounding box: x=136..1307, y=94..947
    # Shield bottom Y found at: 641
    # Let's crop the shield:
    min_x, min_y = 136, 94
    max_x, max_y = 1307, 947
    shield_bottom_y = 641
    
    shield_box = (min_x, min_y, max_x, shield_bottom_y)
    shield_img = img.crop(shield_box)
    
    # Crop to the actual boundaries of the shield itself (remove empty padding)
    s_min_x, s_min_y = shield_img.width, shield_img.height
    s_max_x, s_max_y = 0, 0
    for y in range(shield_img.height):
        for x in range(shield_img.width):
            if shield_img.getpixel((x, y))[3] > 0:
                if x < s_min_x: s_min_x = x
                if x > s_max_x: s_max_x = x
                if y < s_min_y: s_min_y = y
                if y > s_max_y: s_max_y = y
                
    shield_cropped = shield_img.crop((s_min_x, s_min_y, s_max_x + 1, s_max_y + 1))
    os.makedirs("frontend/public", exist_ok=True)
    shield_cropped.save("frontend/public/juricob-shield-light.png")
    print("Transparent light-mode shield saved as frontend/public/juricob-shield-light.png")
    
    # Also save full transparent light logo
    logo_cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    logo_cropped.save("frontend/public/logo-juricob-light-transparent.png")
    print("Transparent full light logo saved as frontend/public/logo-juricob-light-transparent.png")

if __name__ == "__main__":
    process_logo_light()
