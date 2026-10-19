
from pathlib import Path
import json
import time

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "plantvillage" / "extracted"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

# Keep the initial test small for the 8 GB CPU-only laptop.
IMAGE_SIZE = 160
BATCH_SIZE = 8
SMOKE_TRAIN_PER_CLASS = 20
SMOKE_TEST_PER_CLASS = 5
EPOCHS = 1
NUM_WORKERS = 0
SEED = 42


def main():
    torch.manual_seed(SEED)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    train_full = datasets.ImageFolder(DATA_DIR / "train", transform=transform)
    test_full = datasets.ImageFolder(DATA_DIR / "test", transform=transform)

    if train_full.classes != test_full.classes:
        raise RuntimeError("Train/test class mappings do not match.")

    class_to_idx = train_full.class_to_idx
    print(f"Classes: {len(class_to_idx)}")
    print(f"Full training images: {len(train_full)}")
    print(f"Full test images: {len(test_full)}")

    # Select a deterministic, small, balanced subset for the smoke test.
    generator = torch.Generator().manual_seed(SEED)

    def balanced_subset(dataset, per_class):
        selected = []
        targets = dataset.targets
        for class_id in range(len(dataset.classes)):
            indices = [i for i, target in enumerate(targets) if target == class_id]
            order = torch.randperm(len(indices), generator=generator).tolist()
            selected.extend(indices[i] for i in order[:min(per_class, len(indices))])
        return Subset(dataset, selected)

    train_data = balanced_subset(train_full, SMOKE_TRAIN_PER_CLASS)
    test_data = balanced_subset(test_full, SMOKE_TEST_PER_CLASS)

    train_loader = DataLoader(
        train_data, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS,
    )
    test_loader = DataLoader(
        test_data, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS,
    )

    print(f"Smoke-test training images: {len(train_data)}")
    print(f"Smoke-test test images: {len(test_data)}")
    print("Loading pretrained MobileNetV2 weights...")

    try:
        weights = models.MobileNet_V2_Weights.DEFAULT
        model = models.mobilenet_v2(weights=weights)
    except Exception as exc:
        raise RuntimeError(
            "Could not load pretrained MobileNetV2 weights. "
            "Check internet access and retry; no random-weight fallback was used."
        ) from exc

    for parameter in model.features.parameters():
        parameter.requires_grad = False

    model.classifier[1] = nn.Linear(
        model.last_channel, len(class_to_idx)
    )
    model = model.to("cpu")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        model.classifier.parameters(), lr=1e-3
    )

    started = time.time()

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0
        correct = 0
        seen = 0

        for batch_index, (images, labels) in enumerate(train_loader, start=1):
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * labels.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            seen += labels.size(0)

            if batch_index % 10 == 0 or batch_index == len(train_loader):
                print(
                    f"Epoch {epoch + 1}/{EPOCHS} "
                    f"batch {batch_index}/{len(train_loader)}",
                    flush=True,
                )

        print(
            f"Train loss: {total_loss / seen:.4f} | "
            f"Train accuracy: {correct / seen:.4f}"
        )

    model.eval()
    test_correct = 0
    test_seen = 0

    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images)
            test_correct += (outputs.argmax(1) == labels).sum().item()
            test_seen += labels.size(0)

    test_accuracy = test_correct / test_seen if test_seen else 0.0
    elapsed = time.time() - started

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "class_to_idx": class_to_idx,
        "image_size": IMAGE_SIZE,
        "architecture": "mobilenet_v2",
        "smoke_test": True,
    }
    model_path = MODEL_DIR / "plant_disease_smoke_test.pth"
    torch.save(checkpoint, model_path)

    report = {
        "purpose": "smoke_test_only",
        "classes": len(class_to_idx),
        "train_images": len(train_data),
        "test_images": len(test_data),
        "test_accuracy": test_accuracy,
        "elapsed_seconds": round(elapsed, 2),
    }
    report_path = REPORT_DIR / "plant_disease_smoke_test.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Smoke-test test accuracy: {test_accuracy:.4f}")
    print(f"Elapsed seconds: {elapsed:.2f}")
    print(f"Checkpoint: {model_path}")
    print(f"Report: {report_path}")
    print("Smoke test complete. This is not the final trained model.")


if __name__ == "__main__":
    main()
