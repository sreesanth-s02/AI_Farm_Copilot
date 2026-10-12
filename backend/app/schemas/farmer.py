from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import Language


class FarmerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=15)
    preferred_language: Language = Language.TA


class FarmerResponse(BaseModel):
    id: int
    name: str
    phone: str
    preferred_language: Language
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)