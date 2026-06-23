import os
from PIL import Image

def find_and_crop():
    if not os.path.exists("landing.png"):
        print("landing.png not found")
        return
        
    img = Image.open("landing.png")
    width, height = img.size
    print(f"Image loaded: {width}x{height}")
    
    # We want to find the team photo which is located below the hero section.
    # The hero section ends where the dark blue background transitions to white.
    # Let's find the y-coordinate where the background becomes white.
    
    # Let's scan down the middle of the image to find the transition from dark to white.
    y_transition = 0
    for y in range(int(height * 0.2), int(height * 0.6)):
        # Check a few horizontal pixels to make sure it's white
        pixels = [img.getpixel((x, y)) for x in range(int(width * 0.1), int(width * 0.9), int(width * 0.1))]
        # If all checked pixels are white (or very close to white)
        is_white_row = all(sum(p[:3]) > 750 for p in pixels) # 250*3 = 750
        if is_white_row:
            y_transition = y
            break
            
    print(f"White background transition starts at y = {y_transition}")
    
    # The team photo is in the white section, on the left side (x between 0 and width * 0.5)
    # Let's find the bounding box of the non-white rectangular image in this area
    # We scan rows from y_transition downwards
    
    min_x, min_y, max_x, max_y = width, height, 0, 0
    found_box = False
    
    # Let's scan the left half of the image below y_transition
    for y in range(y_transition + 10, int(height * 0.6)):
        row_has_non_white = False
        for x in range(int(width * 0.05), int(width * 0.45)):
            p = img.getpixel((x, y))
            # If not white (sum < 740)
            if sum(p[:3]) < 745:
                row_has_non_white = True
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                
    print(f"Found candidate bounding box: x={min_x}..{max_x}, y={min_y}..{max_y}")
    
    if max_x > min_x and max_y > min_y:
        # Add a tiny margin or crop exactly
        # Let's inspect the cropped region
        cropped = img.crop((min_x - 2, min_y - 2, max_x + 2, max_y + 2))
        os.makedirs("frontend/public", exist_ok=True)
        cropped.save("frontend/public/juricob-team-three.png")
        print("Cropped team photo saved as frontend/public/juricob-team-three.png")
    else:
        print("Could not find team bounding box")

if __name__ == "__main__":
    find_and_crop()
