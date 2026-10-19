
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.disease_service import disease_service


router = APIRouter(prefix="/api/disease", tags=["Plant Disease"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/predict")
async def predict_disease(image: UploadFile = File(...)):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPEG, PNG, or WebP image.",
        )

    try:
        contents = await image.read(MAX_UPLOAD_BYTES + 1)

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty.",
            )

        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Image must be 10 MB or smaller.",
            )

        result = disease_service.predict(contents)
        return {
            "status": "success",
            "filename": image.filename,
            **result,
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="Disease prediction service is unavailable.",
        ) from exc

    finally:
        await image.close()
