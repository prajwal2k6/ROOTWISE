
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class FieldCreate(BaseModel):
    region_id: int
    farmer_id: int | None = None
    name: str
    boundary_geojson: dict[str, Any]
    centroid_lat: float | None = None
    centroid_lon: float | None = None
    area_hectares: float = Field(gt=0)
    soil_type: str | None = None
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    irrigation_type: str | None = None


class FieldUpdate(BaseModel):
    region_id: int | None = None
    farmer_id: int | None = None
    name: str | None = None
    boundary_geojson: dict[str, Any] | None = None
    centroid_lat: float | None = None
    centroid_lon: float | None = None
    area_hectares: float | None = Field(default=None, gt=0)
    soil_type: str | None = None
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    irrigation_type: str | None = None


class FieldResponse(BaseModel):
    id: int
    region_id: int
    farmer_id: int | None
    name: str
    boundary_geojson: dict[str, Any]
    centroid_lat: float | None
    centroid_lon: float | None
    area_hectares: float
    soil_type: str | None
    soil_ph: float | None
    irrigation_type: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
