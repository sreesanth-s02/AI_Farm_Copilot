
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.irrigation_service import get_irrigation_assessment

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["Recommendations"],
)


@router.get("/irrigation/{field_id}")
def irrigation_recommendation(
    field_id: int,
    db: Session = Depends(get_db),
):
    return get_irrigation_assessment(field_id, db)
