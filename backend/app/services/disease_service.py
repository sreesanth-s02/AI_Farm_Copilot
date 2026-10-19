
import io
import time
from pathlib import Path
from threading import Lock

import torch
from torch import nn
from PIL import Image, UnidentifiedImageError
from torchvision import models, transforms


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "plant_disease_best.pth"

IMAGE_SIZE = 160
MAX_IMAGE_PIXELS = 20_000_000

PREPROCESS = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


class DiseaseService:
    def __init__(self):
        self.model = None
        self.idx_to_class = None
        self.lock = Lock()

    def load_model(self):
        if self.model is not None:
            return

        if not MODEL_PATH.is_file():
            raise RuntimeError(
                f"Disease model checkpoint not found: {MODEL_PATH}"
            )

        checkpoint = torch.load(
            MODEL_PATH,
            map_location="cpu",
            weights_only=True,
        )

        class_to_idx = checkpoint["class_to_idx"]
        idx_to_class = {
            index: name for name, index in class_to_idx.items()
        }

        model = models.mobilenet_v2(weights=None)
        model.classifier[1] = nn.Linear(
            model.last_channel, len(class_to_idx)
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        self.model = model
        self.idx_to_class = idx_to_class

    def predict(self, image_bytes: bytes):
        total_start = time.perf_counter()

        # 1. Model loading (normally only on the first prediction).
        load_start = time.perf_counter()
        self.load_model()
        load_seconds = time.perf_counter() - load_start

        # 2. Image decoding and preprocessing.
        preprocess_start = time.perf_counter()

        try:
            with Image.open(io.BytesIO(image_bytes)) as source:
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Image dimensions are too large.")

                image = source.convert("RGB")
                tensor = PREPROCESS(image).unsqueeze(0)

        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError(
                "Uploaded file is not a valid image."
            ) from exc

        preprocess_seconds = time.perf_counter() - preprocess_start

        # 3. Neural-network inference.
        inference_start = time.perf_counter()

        with self.lock, torch.no_grad():
            probabilities = torch.softmax(
                self.model(tensor), dim=1
            )[0]

            top_probs, top_indices = torch.topk(
                probabilities,
                k=min(3, len(self.idx_to_class)),
            )

        inference_seconds = time.perf_counter() - inference_start

        # 4. Format the top predictions.
        predictions = [
            {
                "class_name": self.idx_to_class[index],
                "probability": round(float(probability), 6),
            }
            for probability, index in zip(
                top_probs.tolist(), top_indices.tolist()
            )
        ]

        total_seconds = time.perf_counter() - total_start

        print(
            "[DISEASE_TIMING] "
            f"model_load={load_seconds:.3f}s | "
            f"preprocess={preprocess_seconds:.3f}s | "
            f"inference={inference_seconds:.3f}s | "
            f"backend_total={total_seconds:.3f}s",
            flush=True,
        )

        return {
            "predicted_class": predictions[0]["class_name"],
            "model_probability": predictions[0]["probability"],
            "top_predictions": predictions,
            "disclaimer": (
                "Prototype prediction, not a confirmed diagnosis. "
                "Scores are model probabilities, not verified diagnostic "
                "confidence. Performance may be lower on real farm images."
            ),
        }


disease_service = DiseaseService()
