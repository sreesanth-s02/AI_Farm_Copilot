
from pathlib import Path
import json
import random
import time

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "plantvillage" / "extracted"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

IMAGE_SIZE = 160
BATCH_SIZE = 8
EPOCHS = 3
TRAIN_PER_CLASS = 300
VAL_PER_CLASS = 30
NUM_WORKERS = 0
SEED = 42


def main():
    random.seed(SEED)
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

    full_train = datasets.ImageFolder(DATA_DIR / "train", transform=transform)
    test_dataset = datasets.ImageFolder(DATA_DIR / "test", transform=transform)

    if full_train.classes != test_dataset.classes:
        raise RuntimeError("Training and test class mappings differ.")

    class_to_idx = full_train.class_to_idx
    targets = full_train.targets
    train_indices = []
    val_indices = []

    for class_id in range(len(full_train.classes)):
        indices = [i for i, target in enumerate(targets) if target == class_id]
        random.shuffle(indices)
        val_count = min(VAL_PER_CLASS, max(1, len(indices) // 5))
        train_count = min(TRAIN_PER_CLASS, len(indices) - val_count)

        val_indices.extend(indices[:val_count])
        train_indices.extend(indices[val_count:val_count + train_count])

    train_dataset = Subset(full_train, train_indices)
    val_dataset = Subset(full_train, val_indices)

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS,
    )

    print(f"Classes: {len(class_to_idx)}")
    print(f"Training images: {len(train_dataset)}")
    print(f"Validation images: {len(val_dataset)}")
    print("Loading pretrained MobileNetV2...")

    model = models.mobilenet_v2(
        weights=models.MobileNet_V2_Weights.DEFAULT
    )

    for parameter in model.features.parameters():
        parameter.requires_grad = False

    model.classifier[1] = nn.Linear(model.last_channel, len(class_to_idx))
    model = model.cpu()

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=1e-3)

    best_val_accuracy = 0.0
    history = []
    start_time = time.time()

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        train_correct = 0
        train_seen = 0

        for batch_num, (images, labels) in enumerate(train_loader, start=1):
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * labels.size(0)
            train_correct += (outputs.argmax(1) == labels).sum().item()
            train_seen += labels.size(0)

            if batch_num % 25 == 0 or batch_num == len(train_loader):
                print(
                    f"Epoch {epoch}/{EPOCHS}: "
                    f"batch {batch_num}/{len(train_loader)}",
                    flush=True,
                )

        model.eval()
        val_correct = 0
        val_seen = 0

        with torch.no_grad():
            for images, labels in val_loader:
                outputs = model(images)
                val_correct += (outputs.argmax(1) == labels).sum().item()
                val_seen += labels.size(0)

        train_loss = total_loss / max(train_seen, 1)
        train_accuracy = train_correct / max(train_seen, 1)
        val_accuracy = val_correct / max(val_seen, 1)

        metrics = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_accuracy": round(train_accuracy, 4),
            "validation_accuracy": round(val_accuracy, 4),
        }
        history.append(metrics)
        print(metrics, flush=True)

        checkpoint = {
            "model_state_dict": model.state_dict(),
            "class_to_idx": class_to_idx,
            "image_size": IMAGE_SIZE,
            "architecture": "mobilenet_v2",
            "epoch": epoch,
            "metrics": metrics,
        }

        torch.save(checkpoint, MODEL_DIR / "plant_disease_latest.pth")

        if val_accuracy >= best_val_accuracy:
            best_val_accuracy = val_accuracy
            torch.save(checkpoint, MODEL_DIR / "plant_disease_best.pth")

        (REPORT_DIR / "plant_disease_training.json").write_text(
            json.dumps({
                "dataset": "PlantVillage",
                "training_subset_per_class": TRAIN_PER_CLASS,
                "validation_subset_per_class": VAL_PER_CLASS,
                "test_set_used_during_training": False,
                "history": history,
                "elapsed_seconds": round(time.time() - start_time, 2),
            }, indent=2),
            encoding="utf-8",
        )

    print(f"Best validation accuracy: {best_val_accuracy:.4f}")
    print(f"Elapsed seconds: {time.time() - start_time:.2f}")
    print("Training run complete. Official test set was not used.")


if __name__ == "__main__":
    main()
