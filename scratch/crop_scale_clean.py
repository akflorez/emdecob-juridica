import os
from PIL import Image

def crop_scale_clean():
    if not os.path.exists("landing.png"):
        print("landing.png not found")
        return
        
    img = Image.open("landing.png")
    # Clean coordinates:
    box = (700, 1275, 1024, 1458)
    cropped = img.crop(box)
    
    os.makedirs("frontend/public", exist_ok=True)
    cropped.save("frontend/public/juricob-contact-scale.png")
    print("Clean cropped contact scale image saved as frontend/public/juricob-contact-scale.png")

if __name__ == "__main__":
    crop_scale_clean()
