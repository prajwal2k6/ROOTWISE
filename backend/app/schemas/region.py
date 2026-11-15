
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class RegionBase(BaseModel):
    code: str
    name: str
    district: str | None = None
    state: str = "Karnataka"
    country: str = "India"
    boundary_geojson: dict[str, Any] | None = None
    centroid_lat: float | None = None
    centroid_lon: float | None = None
    area_hectares: float | None = None


class RegionCreate(RegionBase):
    pass


class RegionUpdate(BaseModel):
    name: str | None = None
    district: str | None = None
    boundary_geojson: dict[str, Any] | None = None
    centroid_lat: float | None = None
    centroid_lon: float | None = None
    area_hectares: float | None = None


class RegionResponse(RegionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
