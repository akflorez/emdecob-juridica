import os
from PIL import Image

def process_logo():
    logo_path = "logo juricob.png"
    if not os.path.exists(logo_path):
        print(f"{logo_path} not found")
        return
        
    img = Image.open(logo_path).convert("RGBA")
    width, height = img.size
    print(f"Logo loaded: {width}x{height}")
    
    # Let's convert the black background to transparent.
    # We will define a threshold for "black" pixels.
    # In standard black-background logos, the background is exactly (0, 0, 0) or very close.
    datas = img.getdata()
    new_data = []
    
    for item in datas:
        # Check if it is close to black (R < 15, G < 15, B < 15)
        if item[0] < 15 and item[1] < 15 and item[2] < 15:
            new_data.append((0, 0, 0, 0)) # Fully transparent
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    # Now let's find the bounding boxes of the non-transparent parts.
    # 1. Bounding box of the shield (which is at the top)
    # 2. Bounding box of the text "JURICOB"
    # 3. Bounding box of the subtext "PORTAL JURÍDICO"
    
    # We can scan from top to bottom
    min_x, min_y = width, height
    max_x, max_y = 0, 0
    
    # Let's find the overall bounding box first
    for y in range(height):
        for x in range(width):
            p = img.getpixel((x, y))
            if p[3] > 0: # Not transparent
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                
    print(f"Overall bounding box: x={min_x}..{max_x}, y={min_y}..{max_y}")
    
    # Let's isolate the shield. The shield is at the top, and there is a blank row 
    # of transparent pixels between the shield and the text "JURICOB".
    # Let's find this blank row. We scan y from min_y to max_y.
    shield_bottom_y = 0
    for y in range(min_y, max_y):
        row_is_empty = True
        for x in range(min_x, max_x + 1):
            if img.getpixel((x, y))[3] > 0:
                row_is_empty = False
                break
        if row_is_empty and y > (min_y + 100):
            # We found an empty row below the shield!
            shield_bottom_y = y
            break
            
    print(f"Shield bottom Y found at: {shield_bottom_y}")
    
    # Crop the shield
    if shield_bottom_y > 0:
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
                    if y < s_min_y: s_min_y = s_min_y = y
                    if y > s_max_y: s_max_y = y
        
        shield_cropped = shield_img.crop((s_min_x, s_min_y, s_max_x + 1, s_max_y + 1))
        os.makedirs("frontend/public", exist_ok=True)
        shield_cropped.save("frontend/public/juricob-shield.png")
        print("Transparent shield saved as frontend/public/juricob-shield.png")
        
    # Crop the full transparent logo (cropped to its bounding box)
    logo_cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    logo_cropped.save("frontend/public/logo-juricob-transparent.png")
    print("Transparent full logo saved as frontend/public/logo-juricob-transparent.png")

if __name__ == "__main__":
    process_logo()
