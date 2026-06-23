import os
from PIL import Image, ImageDraw, ImageFont

def draw_grid():
    if not os.path.exists("landing.png"):
        print("landing.png not found")
        return
        
    img = Image.open("landing.png")
    width, height = img.size
    
    # Create a copy to draw on
    draw_img = img.copy()
    draw = ImageDraw.Draw(draw_img)
    
    # Draw horizontal lines and text
    for y in range(0, height, 50):
        color = (255, 0, 0) if y % 100 == 0 else (200, 100, 100)
        draw.line([(0, y), (width, y)], fill=color, width=1)
        if y % 100 == 0:
            draw.text((10, y + 2), f"Y={y}", fill=(255, 0, 0))
            
    # Draw vertical lines and text
    for x in range(0, width, 50):
        color = (0, 0, 255) if x % 100 == 0 else (100, 100, 200)
        draw.line([(x, 0), (x, height)], fill=color, width=1)
        if x % 100 == 0:
            draw.text((x + 2, 10), f"X={x}", fill=(0, 0, 255))
            
    os.makedirs("scratch", exist_ok=True)
    draw_img.save("scratch/landing_grid.png")
    print("Grid image saved as scratch/landing_grid.png")

if __name__ == "__main__":
    draw_grid()
