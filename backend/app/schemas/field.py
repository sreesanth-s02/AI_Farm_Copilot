from pydantic import BaseModel, ConfigDict, Field


class FieldCreate(BaseModel):
    farm_id: int
    field_name: str = Field(min_length=2, max_length=100)
    area_acres: float = Field(gt=0)
    soil_type: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class FieldResponse(BaseModel):
    id: int
    farm_id: int
    field_name: str
    area_acres: float
    soil_type: str | None
    latitude: float | None
    longitude: float | None

    model_config = ConfigDict(from_attributes=True)