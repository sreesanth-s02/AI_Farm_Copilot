from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.crop import Crop
from app.models.field import Field
from app.schemas.crop import CropCreate, CropResponse


router = APIRouter(
    prefix="/api/v1/crops",
    tags=["Crops"]
)


@router.post(
    "",
    response_model=CropResponse,
    status_code=201
)
def create_crop(
    crop_data: CropCreate,
    db: Session = Depends(get_db)
):
    field = db.get(Field, crop_data.field_id)

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    crop = Crop(
        field_id=crop_data.field_id,
        crop_name=crop_data.crop_name,
        variety=crop_data.variety,
        sowing_date=crop_data.sowing_date,
        expected_harvest_date=crop_data.expected_harvest_date,
        growth_stage=crop_data.growth_stage,
        status=crop_data.status
    )

    db.add(crop)
    db.commit()
    db.refresh(crop)

    return crop


@router.get(
    "/{crop_id}",
    response_model=CropResponse
)
def get_crop(
    crop_id: int,
    db: Session = Depends(get_db)
):
    crop = db.get(Crop, crop_id)

    if crop is None:
        raise HTTPException(
            status_code=404,
            detail="Crop not found"
        )

    return crop


@router.get(
    "/field/{field_id}",
    response_model=list[CropResponse]
)
def get_field_crops(
    field_id: int,
    db: Session = Depends(get_db)
):
    field = db.get(Field, field_id)

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    crops = db.scalars(
        select(Crop)
        .where(Crop.field_id == field_id)
    ).all()

    return crops