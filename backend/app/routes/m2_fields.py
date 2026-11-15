"""Authenticated M2 field CRUD scoped to the existing Farmer model."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_verified_supabase_user
from app.database import get_db
from app.models.farmer import Farmer
from app.models.field import Field as FarmField
from app.models.region import Region
from app.schemas.field import FieldResponse

router = APIRouter(prefix="/fields", tags=["M2 Fields"])


class OwnedFieldCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region_id: int
    name: str
    boundary_geojson: dict[str, Any]
    centroid_lat: float | None = Field(default=None, ge=-90, le=90)
    centroid_lon: float | None = Field(default=None, ge=-180, le=180)
    area_hectares: float = Field(gt=0)
    soil_type: str | None = None
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    irrigation_type: str | None = None


class OwnedFieldUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region_id: int | None = None
    name: str | None = None
    boundary_geojson: dict[str, Any] | None = None
    centroid_lat: float | None = Field(default=None, ge=-90, le=90)
    centroid_lon: float | None = Field(default=None, ge=-180, le=180)
    area_hectares: float | None = Field(default=None, gt=0)
    soil_type: str | None = None
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    irrigation_type: str | None = None


def _farmer_for_user(db: Session, user: dict) -> Farmer:
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Account email is required")
    farmer = db.scalar(
        select(Farmer).where(func.lower(Farmer.email) == email.lower())
    )
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return farmer


@router.get("/", response_model=list[FieldResponse])
def list_owned_fields(
    region_id: int | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_verified_supabase_user),
):
    farmer = _farmer_for_user(db, user)
    statement = select(FarmField).where(FarmField.farmer_id == farmer.id)
    if region_id is not None:
        statement = statement.where(FarmField.region_id == region_id)
    return db.scalars(statement.order_by(FarmField.id)).all()


@router.get("/{field_id}", response_model=FieldResponse)
def get_owned_field(
    field_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_verified_supabase_user),
):
    farmer = _farmer_for_user(db, user)
    field = db.scalar(
        select(FarmField).where(
            FarmField.id == field_id,
            FarmField.farmer_id == farmer.id,
        )
    )
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.post(
    "/",
    response_model=FieldResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_owned_field(
    data: OwnedFieldCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_verified_supabase_user),
):
    farmer = _farmer_for_user(db, user)
    if db.get(Region, data.region_id) is None:
        raise HTTPException(status_code=404, detail="Region not found")
    field = FarmField(**data.model_dump(), farmer_id=farmer.id)
    try:
        db.add(field)
        db.commit()
        db.refresh(field)
        return field
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Field conflicts with existing data") from error


@router.patch("/{field_id}", response_model=FieldResponse)
def update_owned_field(
    field_id: int,
    data: OwnedFieldUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_verified_supabase_user),
):
    farmer = _farmer_for_user(db, user)
    field = db.scalar(
        select(FarmField).where(
            FarmField.id == field_id,
            FarmField.farmer_id == farmer.id,
        )
    )
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    updates = data.model_dump(exclude_unset=True)
    if "region_id" in updates and updates["region_id"] is None:
        raise HTTPException(status_code=422, detail="region_id cannot be null")
    if "area_hectares" in updates and updates["area_hectares"] is None:
        raise HTTPException(status_code=422, detail="area_hectares cannot be null")
    if "name" in updates and updates["name"] is None:
        raise HTTPException(status_code=422, detail="name cannot be null")
    if "boundary_geojson" in updates and updates["boundary_geojson"] is None:
        raise HTTPException(status_code=422, detail="boundary_geojson cannot be null")
    if "region_id" in updates and db.get(Region, updates["region_id"]) is None:
        raise HTTPException(status_code=404, detail="Region not found")
    for key, value in updates.items():
        setattr(field, key, value)
    try:
        db.commit()
        db.refresh(field)
        return field
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Field update conflicts with existing data",
        ) from error


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owned_field(
    field_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_verified_supabase_user),
):
    farmer = _farmer_for_user(db, user)
    field = db.scalar(
        select(FarmField).where(
            FarmField.id == field_id,
            FarmField.farmer_id == farmer.id,
        )
    )
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")
    try:
        db.delete(field)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Field is referenced by related records",
        ) from error
    return None
