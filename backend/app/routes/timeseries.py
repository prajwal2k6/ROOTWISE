
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.region import Region
from app.models.climate_feature import ClimateFeature


router = APIRouter(tags=["Time-Series APIs"])


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


@router.get("/timeseries/regions/{region_code}/climate")
def get_climate_timeseries(
    region_code: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    source: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Return date-wise climate averages for a region.

    Only existing non-null indicator values contribute to averages.
    """

    region = get_region(db, region_code)

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be later than end_date.",
        )

    conditions = [
        ClimateFeature.region_id == region.id,
        ClimateFeature.map_cell_id.is_not(None),
    ]

    if start_date is not None:
        conditions.append(
            ClimateFeature.feature_date >= start_date
        )

    if end_date is not None:
        conditions.append(
            ClimateFeature.feature_date <= end_date
        )

    if source is not None:
        conditions.append(
            ClimateFeature.source == source
        )

    statement = (
        select(
            ClimateFeature.feature_date,
            func.count(ClimateFeature.id).label("observation_count"),
            func.avg(ClimateFeature.rainfall_mm).label("avg_rainfall_mm"),
            func.avg(ClimateFeature.soil_moisture_pct).label("avg_soil_moisture_pct"),
            func.avg(ClimateFeature.temperature_min_c).label("avg_temperature_min_c"),
            func.avg(ClimateFeature.temperature_max_c).label("avg_temperature_max_c"),
            func.avg(ClimateFeature.humidity_pct).label("avg_humidity_pct"),
            func.avg(ClimateFeature.ndvi).label("avg_ndvi"),
            func.avg(ClimateFeature.evapotranspiration_mm).label("avg_evapotranspiration_mm"),
        )
        .where(*conditions)
        .group_by(ClimateFeature.feature_date)
        .order_by(ClimateFeature.feature_date)
    )

    results = db.execute(statement).all()

    def safe_average(value):
        return round(float(value), 4) if value is not None else None

    time_series = []

    for row in results:
        time_series.append({
            "date": row.feature_date.isoformat(),
            "observation_count": row.observation_count,
            "indicators": {
                "rainfall_mm": safe_average(row.avg_rainfall_mm),
                "soil_moisture_pct": safe_average(row.avg_soil_moisture_pct),
                "temperature_min_c": safe_average(row.avg_temperature_min_c),
                "temperature_max_c": safe_average(row.avg_temperature_max_c),
                "humidity_pct": safe_average(row.avg_humidity_pct),
                "ndvi": safe_average(row.avg_ndvi),
                "evapotranspiration_mm": safe_average(
                    row.avg_evapotranspiration_mm
                ),
            },
        })

    return {
        "status": "success",
        "region": {
            "code": region.code,
            "name": region.name,
        },
        "filters": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "source": source,
        },
        "total_dates": len(time_series),
        "time_series": time_series,
    }


@router.get("/timeseries/regions/{region_code}/indicators")
def get_available_indicators(
    region_code: str,
    db: Session = Depends(get_db),
):
    """Return climate indicators and their available observation counts."""

    region = get_region(db, region_code)

    indicator_columns = {
        "rainfall_mm": ClimateFeature.rainfall_mm,
        "soil_moisture_pct": ClimateFeature.soil_moisture_pct,
        "temperature_min_c": ClimateFeature.temperature_min_c,
        "temperature_max_c": ClimateFeature.temperature_max_c,
        "humidity_pct": ClimateFeature.humidity_pct,
        "ndvi": ClimateFeature.ndvi,
        "evapotranspiration_mm": ClimateFeature.evapotranspiration_mm,
    }

    indicators = []

    for name, column in indicator_columns.items():
        count = db.scalar(
            select(func.count(column)).where(
                ClimateFeature.region_id == region.id,
                ClimateFeature.map_cell_id.is_not(None),
            )
        )

        indicators.append({
            "indicator": name,
            "available_observations": count or 0,
            "has_data": (count or 0) > 0,
        })

    return {
        "status": "success",
        "region": region.name,
        "indicators": indicators,
    }
