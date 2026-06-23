import os
from PIL import Image

def crop_scale():
    if not os.path.exists("landing.png"):
        print("landing.png not found")
        return
        
    img = Image.open("landing.png")
    # Coordinates from grid image for the contact scale illustration:
    # Left edge ~ 700, Right edge ~ 1024 (full width)
    # Top edge ~ 1250, Bottom edge ~ 1460
    box = (700, 1250, 1024, 1460)
    cropped = img.crop(box)
    
    os.makedirs("frontend/public", exist_ok=True)
    cropped.save("frontend/public/juricob-contact-scale.png")
    print("Cropped contact scale image saved as frontend/public/juricob-contact-scale.png")

if __name__ == "__main__":
    crop_scale()
