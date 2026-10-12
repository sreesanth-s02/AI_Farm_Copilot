from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.field import Field
from app.models.soil import SoilReading
from app.schemas.soil import SoilReadingCreate, SoilReadingResponse


router = APIRouter(
    prefix="/api/v1/soil",
    tags=["Soil"]
)


@router.post(
    "",
    response_model=SoilReadingResponse,
    status_code=201
)
def create_soil_reading(
    soil_data: SoilReadingCreate,
    db: Session = Depends(get_db)
):
    field = db.get(Field, soil_data.field_id)

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    reading = SoilReading(
        field_id=soil_data.field_id,
        nitrogen=soil_data.nitrogen,
        phosphorus=soil_data.phosphorus,
        potassium=soil_data.potassium,
        ph=soil_data.ph,
        moisture=soil_data.moisture,
        organic_carbon=soil_data.organic_carbon
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    return reading


@router.get(
    "/{reading_id}",
    response_model=SoilReadingResponse
)
def get_soil_reading(
    reading_id: int,
    db: Session = Depends(get_db)
):
    reading = db.get(SoilReading, reading_id)

    if reading is None:
        raise HTTPException(
            status_code=404,
            detail="Soil reading not found"
        )

    return reading


@router.get(
    "/field/{field_id}",
    response_model=list[SoilReadingResponse]
)
def get_field_soil_readings(
    field_id: int,
    db: Session = Depends(get_db)
):
    field = db.get(Field, field_id)

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    readings = db.scalars(
        select(SoilReading)
        .where(SoilReading.field_id == field_id)
        .order_by(SoilReading.recorded_at.desc())
    ).all()

    return readings