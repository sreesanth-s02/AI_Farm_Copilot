
from pathlib import Path
from collections import Counter
from PIL import Image

BASE = Path(__file__).resolve().parents[1] / "data" / "plantvillage" / "extracted"

for split in ("train", "test"):
    split_dir = BASE / split
    class_dirs = sorted(p for p in split_dir.iterdir() if p.is_dir())
    counts = Counter()
    invalid_images = []

    for class_dir in class_dirs:
        images = list(class_dir.glob("*.jpg"))
        counts[class_dir.name] = len(images)

        for image_path in images:
            try:
                with Image.open(image_path) as image:
                    image.verify()
            except Exception:
                invalid_images.append(str(image_path))

    print(f"\n{split.upper()}")
    print(f"Classes: {len(class_dirs)}")
    print(f"Images: {sum(counts.values())}")
    print(f"Invalid images: {len(invalid_images)}")

    if invalid_images:
        print("Examples:", invalid_images[:5])

print("\nVerification complete.")
