
from pathlib import Path
import argparse

import torch
from torch import nn
from PIL import Image
from torchvision import models, transforms

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "plant_disease_best.pth"

IMAGE_SIZE = 160


def load_model():
    checkpoint = torch.load(
        MODEL_PATH,
        map_location="cpu",
        weights_only=True,
    )

    class_to_idx = checkpoint["class_to_idx"]
    idx_to_class = {index: name for name, index in class_to_idx.items()}

    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(
        model.last_channel, len(class_to_idx)
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return model, idx_to_class


def main():
    parser = argparse.ArgumentParser(
        description="Predict a PlantVillage leaf disease class."
    )
    parser.add_argument("image_path", help="Path to a leaf image")
    args = parser.parse_args()

    image_path = Path(args.image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    model, idx_to_class = load_model()

    with Image.open(image_path) as image:
        image = image.convert("RGB")
        tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        probabilities = torch.softmax(model(tensor), dim=1)[0]
        top_probs, top_indices = torch.topk(
            probabilities, k=min(3, len(idx_to_class))
        )

    print(f"\nImage: {image_path}")
    print("Top predictions:")

    for probability, index in zip(top_probs.tolist(), top_indices.tolist()):
        print(f"  {idx_to_class[index]}: {probability:.2%}")

    print(
        "\nNote: scores are model probabilities, not verified "
        "diagnostic confidence. This model was trained on a subset "
        "of PlantVillage and may perform worse on real farm photos."
    )


if __name__ == "__main__":
    main()
