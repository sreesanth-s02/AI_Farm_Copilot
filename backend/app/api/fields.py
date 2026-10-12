from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.farm import Farm
from app.models.field import Field
from app.schemas.field import FieldCreate, FieldResponse


router = APIRouter(
    prefix="/api/v1/fields",
    tags=["Fields"]
)


@router.post("", response_model=FieldResponse, status_code=201)
def create_field(
    field_data: FieldCreate,
    db: Session = Depends(get_db)
):
    farm = db.get(Farm, field_data.farm_id)

    if farm is None:
        raise HTTPException(
            status_code=404,
            detail="Farm not found"
        )

    field = Field(
        farm_id=field_data.farm_id,
        field_name=field_data.field_name,
        area_acres=field_data.area_acres,
        soil_type=field_data.soil_type,
        latitude=field_data.latitude,
        longitude=field_data.longitude
    )

    db.add(field)
    db.commit()
    db.refresh(field)

    return field


@router.get("/{field_id}", response_model=FieldResponse)
def get_field(
    field_id: int,
    db: Session = Depends(get_db)
):
    field = db.get(Field, field_id)

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found"
        )

    return field


@router.get(
    "/farm/{farm_id}",
    response_model=list[FieldResponse]
)
def get_farm_fields(
    farm_id: int,
    db: Session = Depends(get_db)
):
    farm = db.get(Farm, farm_id)

    if farm is None:
        raise HTTPException(
            status_code=404,
            detail="Farm not found"
        )

    fields = db.scalars(
        select(Field)
        .where(Field.farm_id == farm_id)
    ).all()

    return fields