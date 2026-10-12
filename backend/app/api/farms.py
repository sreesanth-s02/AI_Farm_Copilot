from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.schemas.farm import FarmCreate, FarmResponse


router = APIRouter(
    prefix="/api/v1/farms",
    tags=["Farms"]
)


@router.post(
    "",
    response_model=FarmResponse,
    status_code=201
)
def create_farm(
    farm_data: FarmCreate,
    db: Session = Depends(get_db)
):
    # Check that the farmer exists
    farmer = db.get(Farmer, farm_data.farmer_id)

    if farmer is None:
        raise HTTPException(
            status_code=404,
            detail="Farmer not found"
        )

    farm = Farm(
        farmer_id=farm_data.farmer_id,
        farm_name=farm_data.farm_name,
        district=farm_data.district,
        village=farm_data.village,
        total_area_acres=farm_data.total_area_acres
    )

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


@router.get(
    "/{farm_id}",
    response_model=FarmResponse
)
def get_farm(
    farm_id: int,
    db: Session = Depends(get_db)
):
    farm = db.get(Farm, farm_id)

    if farm is None:
        raise HTTPException(
            status_code=404,
            detail="Farm not found"
        )

    return farm


@router.get(
    "/farmer/{farmer_id}",
    response_model=list[FarmResponse]
)
def get_farmer_farms(
    farmer_id: int,
    db: Session = Depends(get_db)
):
    farmer = db.get(Farmer, farmer_id)

    if farmer is None:
        raise HTTPException(
            status_code=404,
            detail="Farmer not found"
        )

    farms = db.scalars(
        select(Farm).where(
            Farm.farmer_id == farmer_id
        )
    ).all()

    return farms