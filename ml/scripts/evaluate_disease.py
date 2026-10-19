
from pathlib import Path
import json
import time

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from sklearn.metrics import classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "plantvillage" / "extracted"
MODEL_PATH = ROOT / "models" / "plant_disease_best.pth"
REPORT_DIR = ROOT / "reports"

IMAGE_SIZE = 160
BATCH_SIZE = 8
NUM_WORKERS = 0


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    dataset = datasets.ImageFolder(DATA_DIR / "test", transform=transform)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location="cpu",
        weights_only=True,
    )

    class_to_idx = checkpoint["class_to_idx"]
    if dataset.class_to_idx != class_to_idx:
        raise RuntimeError("Test dataset class mapping differs from checkpoint.")

    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.last_channel, len(class_to_idx))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
    )

    y_true = []
    y_pred = []
    started = time.time()

    with torch.no_grad():
        for batch_num, (images, labels) in enumerate(loader, start=1):
            outputs = model(images)
            predictions = outputs.argmax(dim=1)

            y_true.extend(labels.tolist())
            y_pred.extend(predictions.tolist())

            if batch_num % 100 == 0 or batch_num == len(loader):
                print(
                    f"Evaluated batches: {batch_num}/{len(loader)}",
                    flush=True,
                )

    class_names = [
        name for name, index in sorted(
            class_to_idx.items(), key=lambda item: item[1]
        )
    ]

    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(class_names))),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true, y_pred, labels=list(range(len(class_names)))
    )

    summary = {
        "model": "MobileNetV2",
        "checkpoint": str(MODEL_PATH),
        "test_images": len(dataset),
        "classes": len(class_names),
        "overall_accuracy": report["accuracy"],
        "macro_precision": report["macro avg"]["precision"],
        "macro_recall": report["macro avg"]["recall"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "elapsed_seconds": round(time.time() - started, 2),
        "note": (
            "Evaluated on the official PlantVillage test split. "
            "Model was trained on a subset of the training split."
        ),
    }

    output_path = REPORT_DIR / "plant_disease_evaluation.json"
    output_path.write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("\nOFFICIAL TEST-SPLIT RESULTS")
    print(f"Images: {len(dataset)}")
    print(f"Classes: {len(class_names)}")
    print(f"Accuracy: {report['accuracy']:.4f}")
    print(f"Macro precision: {report['macro avg']['precision']:.4f}")
    print(f"Macro recall: {report['macro avg']['recall']:.4f}")
    print(f"Macro F1: {report['macro avg']['f1-score']:.4f}")
    print(f"Weighted F1: {report['weighted avg']['f1-score']:.4f}")
    print(f"Elapsed seconds: {summary['elapsed_seconds']}")
    print(f"Detailed report: {output_path}")


if __name__ == "__main__":
    main()
