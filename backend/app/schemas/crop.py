
from typing import Any
from pydantic import BaseModel, ConfigDict


class CropCreate(BaseModel):
    slug: str
    name: str
    scientific_name: str | None = None
    season: str | None = None
    duration_days: int | None = None
    water_requirement: str | None = None
    water_requirement_mm: float | None = None
    soil_preferences: dict[str, Any] | None = None
    nutrient_needs: dict[str, Any] | None = None
    crop_metadata: dict[str, Any] | None = None
    is_active: bool = True


class CropUpdate(BaseModel):
    name: str | None = None
    scientific_name: str | None = None
    season: str | None = None
    duration_days: int | None = None
    water_requirement: str | None = None
    water_requirement_mm: float | None = None
    soil_preferences: dict[str, Any] | None = None
    nutrient_needs: dict[str, Any] | None = None
    crop_metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class CropResponse(CropCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
