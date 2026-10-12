from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FarmCreate(BaseModel):
    farmer_id: int
    farm_name: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=100)
    village: str | None = Field(default=None, max_length=100)
    total_area_acres: float | None = Field(
        default=None,
        gt=0
    )


class FarmResponse(BaseModel):
    id: int
    farmer_id: int
    farm_name: str
    district: str
    village: str | None
    total_area_acres: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)