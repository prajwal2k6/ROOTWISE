
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.region import Region
from app.models.map_cell import MapCell


router = APIRouter(tags=["Map APIs"])


def get_region(db: Session, region_code: str):
    """Find a region using its unique code."""

    region = db.execute(
        select(Region).where(Region.code == region_code)
    ).scalar_one_or_none()

    if region is None:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region_code}' not found.",
        )

    return region


@router.get("/maps/regions/{region_code}/cells")
def get_region_map_cells(
    region_code: str,
    source_date: date | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Retrieve geographical map cells for a region.

    Returns a GeoJSON FeatureCollection suitable for map display.
    """

    region = get_region(db, region_code)

    conditions = [
        MapCell.region_id == region.id,
    ]

    if source_date is not None:
        conditions.append(
            MapCell.source_date == source_date
        )

    total = db.scalar(
        select(func.count(MapCell.id)).where(*conditions)
    )

    statement = (
        select(MapCell)
        .where(*conditions)
        .order_by(MapCell.cell_code)
        .offset(offset)
        .limit(limit)
    )

    cells = db.scalars(statement).all()

    features = []

    for cell in cells:
        features.append({
            "type": "Feature",
            "id": cell.id,
            "geometry": cell.geometry_geojson,
            "properties": {
                "grid_id": cell.cell_code,
                "centroid_lat": cell.centroid_lat,
                "centroid_lon": cell.centroid_lon,
                "source_date": (
                    cell.source_date.isoformat()
                    if cell.source_date else None
                ),
                "risk_score": cell.risk_score,
                "risk_level": cell.risk_level,
                **(cell.properties or {}),
            },
        })

    return {
        "type": "FeatureCollection",
        "region": {
            "code": region.code,
            "name": region.name,
        },
        "pagination": {
            "total_records": total or 0,
            "offset": offset,
            "limit": limit,
            "returned_records": len(features),
        },
        "features": features,
    }


@router.get("/maps/regions/{region_code}/cells/{cell_code}")
def get_map_cell_details(
    region_code: str,
    cell_code: str,
    db: Session = Depends(get_db),
):
    """Retrieve the geographical details of one map cell."""

    region = get_region(db, region_code)

    cell = db.execute(
        select(MapCell).where(
            MapCell.region_id == region.id,
            MapCell.cell_code == cell_code,
        )
    ).scalar_one_or_none()

    if cell is None:
        raise HTTPException(
            status_code=404,
            detail=f"Map cell '{cell_code}' not found.",
        )

    return {
        "status": "success",
        "region": region.name,
        "grid_id": cell.cell_code,
        "geometry": cell.geometry_geojson,
        "centroid": {
            "latitude": cell.centroid_lat,
            "longitude": cell.centroid_lon,
        },
        "source_date": (
            cell.source_date.isoformat()
            if cell.source_date else None
        ),
        "risk_score": cell.risk_score,
        "risk_level": cell.risk_level,
        "properties": cell.properties or {},
    }
