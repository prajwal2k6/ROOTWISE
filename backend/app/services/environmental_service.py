
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.map_cell import MapCell
from app.models.climate_feature import ClimateFeature


def point_in_ring(lon, lat, ring):
    """Return True when a point is inside a polygon ring."""
    inside = False

    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]

        if (y1 > lat) != (y2 > lat):
            x_intersection = (
                (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            )
            if lon < x_intersection:
                inside = not inside

    return inside


def point_in_geometry(lon, lat, geometry):
    """Support GeoJSON Polygon and MultiPolygon."""
    if not isinstance(geometry, dict):
        return False

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        polygons = [coordinates]
    elif geometry_type == "MultiPolygon":
        polygons = coordinates
    else:
        return False

    for polygon in polygons:
        if not polygon:
            continue

        if point_in_ring(lon, lat, polygon[0]):
            if not any(
                point_in_ring(lon, lat, hole)
                for hole in polygon[1:]
            ):
                return True

    return False


def get_environmental_data(db: Session, field):
    """Find a farm's grid cell and historical observations."""
    if field.centroid_lat is None or field.centroid_lon is None:
        return {
            "status": "missing_coordinates",
            "map_cell": None,
            "observations": [],
        }

    cells = db.scalars(
        select(MapCell).where(
            MapCell.region_id == field.region_id
        )
    ).all()

    matched_cell = next(
        (
            cell for cell in cells
            if point_in_geometry(
                field.centroid_lon,
                field.centroid_lat,
                cell.geometry_geojson,
            )
        ),
        None,
    )

    if matched_cell is None:
        return {
            "status": "no_matching_cell",
            "map_cell": None,
            "observations": [],
        }

    observations = db.scalars(
        select(ClimateFeature)
        .where(ClimateFeature.map_cell_id == matched_cell.id)
        .order_by(ClimateFeature.feature_date.desc())
    ).all()

    return {
        "status": "matched",
        "map_cell": {
            "id": matched_cell.id,
            "cell_code": matched_cell.cell_code,
        },
        "observations": [
            {
                "date": obs.feature_date.isoformat(),
                "source": obs.source,
                "rainfall_mm": obs.rainfall_mm,
                "temperature_min_c": obs.temperature_min_c,
                "temperature_max_c": obs.temperature_max_c,
                "humidity_pct": obs.humidity_pct,
                "soil_moisture_pct": obs.soil_moisture_pct,
                "ndvi": obs.ndvi,
                "evapotranspiration_mm": obs.evapotranspiration_mm,
                "data_quality": obs.data_quality,
            }
            for obs in observations
        ],
    }
