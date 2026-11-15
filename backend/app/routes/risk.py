
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.region import Region
from app.models.map_cell import MapCell


router = APIRouter(tags=["Risk APIs"])


def get_region(db: Session, region_code: str):
    region = db.execute(
        select(Region).where(Region.code == region_code)
    ).scalar_one_or_none()

    if region is None:
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region_code}' not found.",
        )

    return region


@router.get("/risk/regions/{region_code}/summary")
def get_region_risk_summary(
    region_code: str,
    db: Session = Depends(get_db),
):
    """Return a summary of risk values already stored for a region."""

    region = get_region(db, region_code)

    statement = (
        select(
            func.count(MapCell.id).label("total_cells"),
            func.count(MapCell.risk_score).label("assessed_cells"),
            func.avg(MapCell.risk_score).label("average_risk_score"),
        )
        .where(MapCell.region_id == region.id)
    )

    result = db.execute(statement).one()

    level_statement = (
        select(
            MapCell.risk_level,
            func.count(MapCell.id),
        )
        .where(
            MapCell.region_id == region.id,
            MapCell.risk_level.is_not(None),
        )
        .group_by(MapCell.risk_level)
        .order_by(MapCell.risk_level)
    )

    levels = db.execute(level_statement).all()

    return {
        "status": "success",
        "region": region.name,
        "total_cells": result.total_cells,
        "assessed_cells": result.assessed_cells,
        "unassessed_cells": (
            result.total_cells - result.assessed_cells
        ),
        "average_risk_score": (
            round(float(result.average_risk_score), 2)
            if result.average_risk_score is not None
            else None
        ),
        "risk_level_distribution": [
            {
                "risk_level": level,
                "cell_count": count,
            }
            for level, count in levels
        ],
        "message": (
            "Risk values are retrieved from stored map-cell records. "
            "No risk scores are calculated by this endpoint."
        ),
    }


@router.get("/risk/regions/{region_code}/cells")
def get_region_risk_cells(
    region_code: str,
    risk_level: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Retrieve map cells with their stored risk information."""

    region = get_region(db, region_code)

    conditions = [
        MapCell.region_id == region.id,
    ]

    if risk_level is not None:
        conditions.append(
            func.lower(MapCell.risk_level) == risk_level.lower()
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

    return {
        "status": "success",
        "region": region.name,
        "pagination": {
            "total_records": total or 0,
            "offset": offset,
            "limit": limit,
            "returned_records": len(cells),
        },
        "risk_cells": [
            {
                "grid_id": cell.cell_code,
                "risk_score": cell.risk_score,
                "risk_level": cell.risk_level,
                "centroid": {
                    "latitude": cell.centroid_lat,
                    "longitude": cell.centroid_lon,
                },
            }
            for cell in cells
        ],
    }


@router.get("/risk/regions/{region_code}/cells/{cell_code}")
def get_cell_risk_details(
    region_code: str,
    cell_code: str,
    db: Session = Depends(get_db),
):
    """Retrieve stored risk information for one map cell."""

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
        "risk_score": cell.risk_score,
        "risk_level": cell.risk_level,
        "message": (
            "Risk assessment is not available for this cell."
            if cell.risk_score is None and cell.risk_level is None
            else "Stored risk assessment retrieved."
        ),
    }
