from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SoilReadingCreate(BaseModel):
    field_id: int

    nitrogen: float | None = Field(
        default=None,
        ge=0
    )

    phosphorus: float | None = Field(
        default=None,
        ge=0
    )

    potassium: float | None = Field(
        default=None,
        ge=0
    )

    ph: float | None = Field(
        default=None,
        ge=0,
        le=14
    )

    moisture: float | None = Field(
        default=None,
        ge=0,
        le=100
    )

    organic_carbon: float | None = Field(
        default=None,
        ge=0
    )


class SoilReadingResponse(BaseModel):
    id: int
    field_id: int
    nitrogen: float | None
    phosphorus: float | None
    potassium: float | None
    ph: float | None
    moisture: float | None
    organic_carbon: float | None
    recorded_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )