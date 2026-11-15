"""Read-only catalog endpoints for regions and crops."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.crop import Crop
from app.models.region import Region
from app.schemas.crop import CropResponse
from app.schemas.region import RegionResponse

router = APIRouter(tags=["M2 Catalog"])


@router.get("/regions", response_model=list[RegionResponse])
def list_regions(db: Session = Depends(get_db)):
    return db.scalars(select(Region).order_by(Region.id)).all()


@router.get("/regions/{region_id}", response_model=RegionResponse)
def get_region(region_id: int, db: Session = Depends(get_db)):
    region = db.get(Region, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.get("/crops", response_model=list[CropResponse])
def list_crops(
    is_active: bool | None = True,
    db: Session = Depends(get_db),
):
    statement = select(Crop)
    if is_active is not None:
        statement = statement.where(Crop.is_active == is_active)
    return db.scalars(statement.order_by(Crop.name)).all()


@router.get("/crops/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, db: Session = Depends(get_db)):
    crop = db.get(Crop, crop_id)
    if crop is None:
        raise HTTPException(status_code=404, detail="Crop not found")
    return crop
