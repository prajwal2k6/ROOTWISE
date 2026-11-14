
from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    farm_name: str = Field(default="My Farm", max_length=150)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    state: str | None = None
    district: str | None = None

    boundary: list[list[float]] = Field(min_length=3)

    area_acres: float = Field(gt=0)
    area_hectares: float = Field(gt=0)

    soil_type: str | None = None
    irrigation: str | None = None

    main_crop: str | None = None
    other_crops: str | None = None

    sowing_season: str | None = None
    harvest_period: str | None = None

    previous_crop_sequence: str | None = None
    crop_frequency: str | None = None

    priority: str | None = None
    notes: str | None = None


class FarmResponse(BaseModel):
    id: int
    farm_name: str

    latitude: float
    longitude: float

    state: str | None = None
    district: str | None = None

    boundary: list[list[float]]

    area_acres: float
    area_hectares: float

    soil_type: str | None = None
    irrigation: str | None = None

    main_crop: str | None = None
    other_crops: str | None = None

    sowing_season: str | None = None
    harvest_period: str | None = None

    previous_crop_sequence: str | None = None
    crop_frequency: str | None = None

    priority: str | None = None
    notes: str | None = None

    class Config:
        from_attributes = True
