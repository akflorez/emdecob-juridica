import os
from PIL import Image

def crop_exact():
    if not os.path.exists("landing.png"):
        print("landing.png not found")
        return
        
    img = Image.open("landing.png")
    # Coordinates from grid image:
    # Left edge ~ 70, Right edge ~ 432
    # Top edge ~ 440, Bottom edge ~ 600
    box = (70, 440, 432, 600)
    cropped = img.crop(box)
    
    os.makedirs("frontend/public", exist_ok=True)
    cropped.save("frontend/public/juricob-team-three.png")
    print("Exact cropped team photo saved as frontend/public/juricob-team-three.png")

if __name__ == "__main__":
    crop_exact()
