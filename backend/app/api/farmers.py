from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.farmer import Farmer
from app.schemas.farmer import FarmerCreate, FarmerResponse


router = APIRouter(
    prefix="/api/v1/farmers",
    tags=["Farmers"]
)


@router.post(
    "",
    response_model=FarmerResponse,
    status_code=201
)
def create_farmer(
    farmer_data: FarmerCreate,
    db: Session = Depends(get_db)
):
    existing_farmer = db.scalar(
        select(Farmer).where(
            Farmer.phone == farmer_data.phone
        )
    )

    if existing_farmer:
        raise HTTPException(
            status_code=409,
            detail="A farmer with this phone number already exists"
        )

    farmer = Farmer(
        name=farmer_data.name,
        phone=farmer_data.phone,
        preferred_language=farmer_data.preferred_language
    )

    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    return farmer


@router.get(
    "/{farmer_id}",
    response_model=FarmerResponse
)
def get_farmer(
    farmer_id: int,
    db: Session = Depends(get_db)
):
    farmer = db.get(Farmer, farmer_id)

    if farmer is None:
        raise HTTPException(
            status_code=404,
            detail="Farmer not found"
        )

    return farmer