import os
from PIL import Image

base_folder = "Dataset"   # change to your dataset folder name

for root, dirs, files in os.walk(base_folder):
    for file in files:
        if file.lower().endswith(".jfif"):
            jfif_path = os.path.join(root, file)
            jpg_path = jfif_path.rsplit(".", 1)[0] + ".jpg"

            try:
                image = Image.open(jfif_path)
                image.save(jpg_path, "JPEG")
                os.remove(jfif_path)
                print("Converted:", jfif_path, "→", jpg_path)
            except Exception as e:
                print("Error converting", jfif_path, e)

print("\nConversion Completed!")
