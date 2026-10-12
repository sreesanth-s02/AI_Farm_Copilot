
from fastapi import APIRouter, Query

from app.services.weather_service import get_weather

router = APIRouter(
    prefix="/api/v1/weather",
    tags=["Weather"],
)


@router.get("/current")
def get_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    return get_weather(
        latitude=latitude,
        longitude=longitude,
        data_type="current",
    )


@router.get("/hourly")
def get_hourly_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    return get_weather(
        latitude=latitude,
        longitude=longitude,
        data_type="hourly",
    )
