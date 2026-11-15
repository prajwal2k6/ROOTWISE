
import json
import math
from datetime import date
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.region import Region
from app.models.map_cell import MapCell
from app.models.climate_feature import ClimateFeature


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DATASET_PATH = (
    Path(__file__).resolve().parents[3]
    / "m2_deliverables"
    / "bengaluru_urban_20160101.json"
)

BATCH_SIZE = 500

INDICATOR_FIELDS = [
    "rainfall_mm",
    "soil_moisture_pct",
    "temperature_min_c",
    "temperature_max_c",
    "humidity_pct",
    "ndvi",
    "evapotranspiration_mm",
]


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

def validate_number(value, field_name):
    """Validate optional numeric values."""

    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid numeric value: {field_name}")

    if not math.isfinite(value):
        raise ValueError(f"Non-finite value: {field_name}")

    return float(value)


def load_dataset():
    """Load and validate the Bengaluru Urban JSON dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    region_data = dataset.get("region")
    cells = dataset.get("cells")

    if not isinstance(region_data, dict):
        raise ValueError("Region information is missing.")

    if not isinstance(cells, list) or not cells:
        raise ValueError("Dataset contains no grid cells.")

    if not region_data.get("code") or not region_data.get("name"):
        raise ValueError("Region code or name is missing.")

    source = dataset.get("source")

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Dataset source is missing.")

    try:
        feature_date = date.fromisoformat(dataset["data_date"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Invalid or missing dataset date.")

    seen_grid_ids = set()
    validated_cells = []

    for index, cell in enumerate(cells):

        if not isinstance(cell, dict):
            raise ValueError(f"Invalid cell at position {index}.")

        grid_id = cell.get("grid_id")

        if not isinstance(grid_id, str) or not grid_id.strip():
            raise ValueError(f"Missing grid_id at position {index}.")

        if grid_id in seen_grid_ids:
            raise ValueError(f"Duplicate grid_id: {grid_id}")

        seen_grid_ids.add(grid_id)

        geometry = cell.get("geometry")

        if (
            not isinstance(geometry, dict)
            or geometry.get("type") not in ("Polygon", "MultiPolygon")
            or "coordinates" not in geometry
        ):
            raise ValueError(f"Invalid geometry for cell {grid_id}.")

        indicators = cell.get("indicators")

        if not isinstance(indicators, dict):
            raise ValueError(f"Invalid indicators for cell {grid_id}.")

        validated_indicators = {
            field: validate_number(
                indicators.get(field),
                f"{grid_id}.{field}",
            )
            for field in INDICATOR_FIELDS
        }

        validated_cells.append({
            "grid_id": grid_id,
            "geometry": geometry,
            "centroid_lat": validate_number(
                cell.get("centroid_lat"),
                f"{grid_id}.centroid_lat",
            ),
            "centroid_lon": validate_number(
                cell.get("centroid_lon"),
                f"{grid_id}.centroid_lon",
            ),
            "indicators": validated_indicators,
            "data_quality": cell.get("data_quality"),
            "state": cell.get("state"),
            "district": cell.get("district"),
        })

    return dataset, region_data, feature_date, validated_cells


# --------------------------------------------------
# DATA INGESTION
# --------------------------------------------------

def ingest_bengaluru_dataset(db: Session):
    """
    Import Bengaluru Urban map cells and climate observations.

    Existing records are updated instead of duplicated.
    All database changes are committed together.
    """

    try:

        # Load and validate dataset
        dataset, region_data, feature_date, cells = load_dataset()

        source = dataset["source"]

        # ------------------------------------------
        # 1. CREATE OR UPDATE REGION
        # ------------------------------------------

        region_insert = pg_insert(Region).values(
            code=region_data["code"],
            name=region_data["name"],
            district=region_data.get("district"),
            state=region_data.get("state", "Karnataka"),
            country=region_data.get("country", "India"),
        )

        region_statement = (
            region_insert
            .on_conflict_do_update(
                index_elements=[Region.code],
                set_={
                    "name": region_insert.excluded.name,
                    "district": region_insert.excluded.district,
                    "state": region_insert.excluded.state,
                    "country": region_insert.excluded.country,
                },
            )
            .returning(Region.id)
        )

        region_id = db.execute(
            region_statement
        ).scalar_one()

        # ------------------------------------------
        # 2. CREATE OR UPDATE MAP CELLS
        # ------------------------------------------

        map_cell_ids = {}

        for start in range(0, len(cells), BATCH_SIZE):

            batch = cells[start:start + BATCH_SIZE]

            map_cell_rows = [
                {
                    "region_id": region_id,
                    "cell_code": cell["grid_id"],
                    "geometry_geojson": cell["geometry"],
                    "centroid_lat": cell["centroid_lat"],
                    "centroid_lon": cell["centroid_lon"],
                    "source_date": feature_date,
                    "properties": {
                        "state": cell["state"],
                        "district": cell["district"],
                        "data_quality": cell["data_quality"],
                        "resolution_m": dataset.get("resolution_m"),
                    },
                }
                for cell in batch
            ]

            map_insert = pg_insert(MapCell).values(
                map_cell_rows
            )

            map_cell_statement = (
                map_insert
                .on_conflict_do_update(
                    constraint="uq_region_cell",
                    set_={
                        "geometry_geojson": map_insert.excluded.geometry_geojson,
                        "centroid_lat": map_insert.excluded.centroid_lat,
                        "centroid_lon": map_insert.excluded.centroid_lon,
                        "source_date": map_insert.excluded.source_date,
                        "properties": map_insert.excluded.properties,
                    },
                )
                .returning(MapCell.id, MapCell.cell_code)
            )

            results = db.execute(
                map_cell_statement
            ).all()

            for map_cell_id, cell_code in results:
                map_cell_ids[cell_code] = map_cell_id

        if len(map_cell_ids) != len(cells):
            raise ValueError(
                "Not all map cells were inserted or updated."
            )

        # ------------------------------------------
        # 3. PREPARE CLIMATE OBSERVATIONS
        # ------------------------------------------

        source_metadata = {
            "schema_version": dataset.get("schema_version"),
            "crs": dataset.get("crs"),
            "resolution_m": dataset.get("resolution_m"),
            "indicator_metadata": dataset.get(
                "indicator_metadata", {}
            ),
        }

        climate_rows = []

        for cell in cells:

            climate_rows.append({
                "region_id": region_id,
                "field_id": None,
                "map_cell_id": map_cell_ids[cell["grid_id"]],
                "source": source,
                "feature_date": feature_date,
                **cell["indicators"],
                "data_quality": cell["data_quality"],
                "source_metadata": source_metadata,
            })

        # ------------------------------------------
        # 4. INSERT OR UPDATE CLIMATE OBSERVATIONS
        # ------------------------------------------

        for start in range(0, len(climate_rows), BATCH_SIZE):

            batch = climate_rows[start:start + BATCH_SIZE]

            climate_insert = pg_insert(
                ClimateFeature
            ).values(batch)

            climate_statement = (
                climate_insert
                .on_conflict_do_update(
                    index_elements=[
                        ClimateFeature.map_cell_id,
                        ClimateFeature.source,
                        ClimateFeature.feature_date,
                    ],
                    index_where=text(
                        "map_cell_id IS NOT NULL"
                    ),
                    set_={
                        "region_id": climate_insert.excluded.region_id,
                        "rainfall_mm": climate_insert.excluded.rainfall_mm,
                        "temperature_min_c": climate_insert.excluded.temperature_min_c,
                        "temperature_max_c": climate_insert.excluded.temperature_max_c,
                        "humidity_pct": climate_insert.excluded.humidity_pct,
                        "soil_moisture_pct": climate_insert.excluded.soil_moisture_pct,
                        "ndvi": climate_insert.excluded.ndvi,
                        "evapotranspiration_mm": climate_insert.excluded.evapotranspiration_mm,
                        "data_quality": climate_insert.excluded.data_quality,
                        "source_metadata": climate_insert.excluded.source_metadata,
                    },
                )
            )

            db.execute(climate_statement)

        # ------------------------------------------
        # 5. COMMIT TRANSACTION
        # ------------------------------------------

        db.commit()

        return {
            "status": "success",
            "message": "Bengaluru Urban dataset ingested successfully.",
            "region": region_data["name"],
            "source": source,
            "data_date": feature_date.isoformat(),
            "map_cells_processed": len(map_cell_ids),
            "climate_features_processed": len(climate_rows),
        }

    except Exception:
        db.rollback()
        raise
