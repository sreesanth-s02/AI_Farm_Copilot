
import random
import subprocess
import sys
from pathlib import Path

TEST_DIR = Path("data/plantvillage/extracted/test")
PREDICT_SCRIPT = Path("scripts/predict_disease.py")
TARGET = 5
MAX_TRIES = 25

random.seed(42)

images = [
    image
    for image in TEST_DIR.rglob("*")
    if image.suffix.lower() in {".jpg", ".jpeg", ".png"}
]

random.shuffle(images)
correct = []
tested = 0

for image in images:
    if tested >= MAX_TRIES or len(correct) >= TARGET:
        break

    true_label = image.parent.name

    try:
        result = subprocess.run(
            [sys.executable, str(PREDICT_SCRIPT), str(image)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        tested += 1

        if result.returncode != 0:
            print(f"Skipped: {image}")
            continue

        predicted_label = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("Top predictions:"):
                continue
            if line and ":" in line and "%" in line:
                predicted_label = line.split(":", 1)[0]
                break

        if predicted_label == true_label:
            correct.append((image, true_label))
            print(f"\nCORRECT: {true_label}")
            print(f"Image: {image}")
            print(result.stdout)
        else:
            print(
                f"Tested {tested}/{MAX_TRIES}: "
                f"actual={true_label}, predicted={predicted_label}"
            )

    except subprocess.TimeoutExpired:
        print(f"Timed out: {image}")

report = Path("reports")
report.mkdir(parents=True, exist_ok=True)
output_file = report / "demo_images.txt"

with output_file.open("w", encoding="utf-8") as file:
    for image, label in correct:
        file.write(f"Actual label: {label}\n")
        file.write(f"Image path: {image}\n\n")

print(f"\nImages tested: {tested}")
print(f"Correct examples found: {len(correct)}")
print(f"Saved results to: {output_file}")

if not correct:
    print("No correct examples found in this sample. Try more images.")
