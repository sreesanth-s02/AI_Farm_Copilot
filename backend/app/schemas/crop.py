from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CropCreate(BaseModel):
    field_id: int

    crop_name: str = Field(
        min_length=2,
        max_length=100
    )

    variety: str | None = Field(
        default=None,
        max_length=100
    )

    sowing_date: date | None = None

    expected_harvest_date: date | None = None

    growth_stage: str | None = Field(
        default=None,
        max_length=100
    )

    status: str = Field(
        default="ACTIVE",
        min_length=1,
        max_length=20
    )


class CropResponse(BaseModel):
    id: int
    field_id: int
    crop_name: str
    variety: str | None
    sowing_date: date | None
    expected_harvest_date: date | None
    growth_stage: str | None
    status: str

    model_config = ConfigDict(
        from_attributes=True
    )