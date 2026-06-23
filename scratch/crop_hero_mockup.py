import os
from PIL import Image

def crop_hero_mockup():
    if not os.path.exists("landing.png"):
        print("landing.png not found")
        return
        
    img = Image.open("landing.png")
    # Coordinates from grid image for the hero laptop and mobile mockup:
    # Left edge ~ 455, Right edge ~ 985
    # Top edge ~ 48, Bottom edge ~ 305
    box = (455, 48, 985, 305)
    cropped = img.crop(box)
    
    os.makedirs("frontend/public", exist_ok=True)
    cropped.save("frontend/public/juricob-hero-mockup.png")
    print("Cropped hero mockup saved as frontend/public/juricob-hero-mockup.png")

if __name__ == "__main__":
    crop_hero_mockup()
