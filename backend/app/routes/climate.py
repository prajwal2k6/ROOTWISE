
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.region import Region
from app.models.map_cell import MapCell
from app.models.climate_feature import ClimateFeature


router = APIRouter(tags=["Climate APIs"])


def get_region_or_404(db: Session, region_code: str):
    """Find a region using its unique region code."""

    region = db.execute(
        select(Region).where(Region.code == region_code)
    ).scalar_one_or_none()

    if region is None:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region_code}' not found.",
        )

    return region


@router.get("/climate/regions/{region_code}/observations")
def get_climate_observations(
    region_code: str,
    observation_date: date | None = Query(default=None),
    source: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Retrieve climate observations and their corresponding map cells.

    Supports filtering by date and data source, with pagination.
    """

    region = get_region_or_404(db, region_code)

    conditions = [
        ClimateFeature.region_id == region.id,
        ClimateFeature.map_cell_id.is_not(None),
    ]

    if observation_date is not None:
        conditions.append(
            ClimateFeature.feature_date == observation_date
        )

    if source is not None:
        conditions.append(
            ClimateFeature.source == source
        )

    total = db.scalar(
        select(func.count(ClimateFeature.id)).where(*conditions)
    )

    statement = (
        select(ClimateFeature, MapCell)
        .join(
            MapCell,
            ClimateFeature.map_cell_id == MapCell.id,
        )
        .where(*conditions)
        .order_by(MapCell.cell_code)
        .offset(offset)
        .limit(limit)
    )

    results = db.execute(statement).all()

    observations = []

    for climate, cell in results:
        observations.append({
            "grid_id": cell.cell_code,
            "feature_date": climate.feature_date.isoformat(),
            "source": climate.source,
            "centroid": {
                "latitude": cell.centroid_lat,
                "longitude": cell.centroid_lon,
            },
            "geometry": cell.geometry_geojson,
            "indicators": {
                "rainfall_mm": climate.rainfall_mm,
                "soil_moisture_pct": climate.soil_moisture_pct,
                "temperature_min_c": climate.temperature_min_c,
                "temperature_max_c": climate.temperature_max_c,
                "humidity_pct": climate.humidity_pct,
                "ndvi": climate.ndvi,
                "evapotranspiration_mm": climate.evapotranspiration_mm,
            },
            "data_quality": climate.data_quality,
        })

    return {
        "status": "success",
        "region": {
            "code": region.code,
            "name": region.name,
        },
        "filters": {
            "observation_date": (
                observation_date.isoformat()
                if observation_date else None
            ),
            "source": source,
        },
        "pagination": {
            "total_records": total or 0,
            "offset": offset,
            "limit": limit,
            "returned_records": len(observations),
        },
        "observations": observations,
    }


@router.get("/climate/regions/{region_code}/dates")
def get_available_climate_dates(
    region_code: str,
    db: Session = Depends(get_db),
):
    """Return available climate observation dates for a region."""

    region = get_region_or_404(db, region_code)

    statement = (
        select(
            ClimateFeature.feature_date,
            func.count(ClimateFeature.id).label("observation_count"),
        )
        .where(
            ClimateFeature.region_id == region.id,
            ClimateFeature.map_cell_id.is_not(None),
        )
        .group_by(ClimateFeature.feature_date)
        .order_by(ClimateFeature.feature_date)
    )

    results = db.execute(statement).all()

    dates = [
        {
            "date": feature_date.isoformat(),
            "observation_count": observation_count,
        }
        for feature_date, observation_count in results
    ]

    return {
        "status": "success",
        "region": region.name,
        "available_dates": dates,
        "total_dates": len(dates),
    }
