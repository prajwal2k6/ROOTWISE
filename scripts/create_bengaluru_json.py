
from pathlib import Path
import json
import math

import geopandas as gpd
import numpy as np
import xarray as xr
from shapely.geometry import mapping

# ==========================================
# 1. CONFIGURATION
# ==========================================

GRID_FILE = Path("data/grids/india/Karnataka_1km_grid.parquet")

GPM_FILE = Path(
    "data/raw/gpm/"
    "3B-DAY.MS.MRG.3IMERG.20160101-S000000-E235959.V07B.nc4"
)

OUTPUT_FILE = Path("data/outputs/bengaluru_urban_20160101.json")
SAMPLE_FILE = Path("data/outputs/bengaluru_urban_sample_3_cells.json")

DATA_DATE = "2016-01-01"
EXPECTED_CELLS = 2380
EXPECTED_CRS = "EPSG:4326"

INDICATORS = {
    "rainfall_mm": None,
    "soil_moisture_pct": None,
    "temperature_min_c": None,
    "temperature_max_c": None,
    "humidity_pct": None,
    "ndvi": None,
    "evapotranspiration_mm": None
}


# ==========================================
# 2. INPUT VALIDATION
# ==========================================

def check_input_files():
    print("Checking input files...")

    for file in (GRID_FILE, GPM_FILE):
        if not file.exists():
            raise FileNotFoundError(f"File not found: {file}")

    print("Input files: PASSED")


# ==========================================
# 3. LOAD AND VALIDATE GRID
# ==========================================

def load_bengaluru_grid():

    print("\nLoading Karnataka grid...")

    gdf = gpd.read_parquet(GRID_FILE)

    required_columns = {
        "grid_id", "district", "state_name", "geometry"
    }

    missing = required_columns - set(gdf.columns)

    if missing:
        raise ValueError(f"Missing grid columns: {missing}")

    if gdf.crs is None:
        raise ValueError("Grid CRS is not defined.")

    if gdf.geometry.isna().any():
        raise ValueError("Grid contains null geometries.")

    if gdf.geometry.is_empty.any():
        raise ValueError("Grid contains empty geometries.")

    if not gdf.geometry.is_valid.all():
        raise ValueError("Grid contains invalid geometries.")

    gdf = gdf[
        gdf["district"].astype(str).str.strip().str.casefold()
        == "bengaluru urban"
    ].copy()

    if gdf.empty:
        raise ValueError("Bengaluru Urban cells not found.")

    if gdf["grid_id"].isna().any():
        raise ValueError("Missing grid IDs.")

    if gdf["grid_id"].duplicated().any():
        raise ValueError("Duplicate grid IDs.")

    if len(gdf) != EXPECTED_CELLS:
        raise ValueError(
            f"Expected {EXPECTED_CELLS} cells, found {len(gdf)}"
        )

    print("Bengaluru Urban cells:", len(gdf))
    print("Grid CRS:", gdf.crs)
    print("Grid validation: PASSED")

    return gdf


# ==========================================
# 4. PREPARE GEOMETRIES
# ==========================================

def prepare_geometries(gdf):

    print("\nPreparing geometries...")

    centroids = gpd.GeoSeries(
        gdf.geometry.centroid,
        crs=gdf.crs
    ).to_crs(EXPECTED_CRS)

    gdf_geo = gdf.to_crs(EXPECTED_CRS)

    if not gdf_geo.geometry.is_valid.all():
        raise ValueError("Invalid geometry after CRS conversion.")

    return gdf_geo, centroids


# ==========================================
# 5. NASA GPM DATA VALIDATION
# ==========================================

def load_rainfall(centroids):

    print("\nLoading NASA GPM data...")

    with xr.open_dataset(
        GPM_FILE,
        engine="netcdf4"
    ) as ds:

        if "precipitation" not in ds:
            raise ValueError("Precipitation variable not found.")

        rain_data = ds["precipitation"]

        if "time" not in rain_data.dims:
            raise ValueError("GPM time dimension not found.")

        if "lon" not in rain_data.coords:
            raise ValueError("GPM longitude coordinate not found.")

        if "lat" not in rain_data.coords:
            raise ValueError("GPM latitude coordinate not found.")

        units = rain_data.attrs.get("units")

        if units != "mm/day":
            raise ValueError(
                f"Unexpected rainfall units: {units}"
            )

        observation_date = np.datetime_as_string(
            ds["time"].values[0],
            unit="D"
        )

        if observation_date != DATA_DATE:
            raise ValueError(
                f"Expected {DATA_DATE}, got {observation_date}"
            )

        print("NASA product:", "GPM IMERG")
        print("Observation date:", observation_date)
        print("Rainfall units:", units)

        rain = rain_data.isel(time=0)

        lat_points = xr.DataArray(
            centroids.y.to_numpy(),
            dims="cell"
        )

        lon_points = xr.DataArray(
            centroids.x.to_numpy(),
            dims="cell"
        )

        sampled = rain.sel(
            lon=lon_points,
            lat=lat_points,
            method="nearest"
        )

        values = np.asarray(sampled.values, dtype=float)

        if len(values) != len(centroids):
            raise ValueError("Rainfall sample count mismatch.")

        # Copy values before closing the source dataset.
        values = values.copy()

    print("Rainfall samples:", len(values))
    print("NASA data extraction: PASSED")

    return values


# ==========================================
# 6. BUILD INDIVIDUAL GRID CELLS
# ==========================================

def build_cells(gdf_geo, centroids, rainfall_values):

    print("\nBuilding grid cell records...")

    cells = []

    for i, (_, row) in enumerate(gdf_geo.iterrows()):

        value = rainfall_values[i]

        if np.isfinite(value) and value >= 0:

            rainfall = round(float(value), 4)
            quality = "estimated"

        else:

            rainfall = None
            quality = "missing"

        centroid = centroids.iloc[i]

        indicators = INDICATORS.copy()
        indicators["rainfall_mm"] = rainfall

        cell = {
            "grid_id": str(row["grid_id"]),
            "state": str(row["state_name"]),
            "district": str(row["district"]),
            "geometry": mapping(row.geometry),

            "centroid_lat": round(float(centroid.y), 6),
            "centroid_lon": round(float(centroid.x), 6),

            "indicators": indicators,
            "data_quality": quality
        }

        cells.append(cell)

    return cells


# ==========================================
# 7. INDICATOR METADATA
# ==========================================

def create_metadata():

    return {

        "rainfall_mm": {
            "source": "NASA GPM IMERG V07B",
            "units": "mm/day",
            "status": "estimated",
            "native_resolution": "0.1 degree"
        },

        "soil_moisture_pct": {
            "source": None,
            "units": "%",
            "status": "not_integrated"
        },

        "temperature_min_c": {
            "source": None,
            "units": "degree Celsius",
            "status": "not_integrated"
        },

        "temperature_max_c": {
            "source": None,
            "units": "degree Celsius",
            "status": "not_integrated"
        },

        "humidity_pct": {
            "source": None,
            "units": "%",
            "status": "not_integrated"
        },

        "ndvi": {
            "source": None,
            "units": "unitless",
            "status": "not_integrated"
        },

        "evapotranspiration_mm": {
            "source": None,
            "units": "mm",
            "status": "not_integrated"
        }
    }


# ==========================================
# 8. BUILD FINAL JSON
# ==========================================

def build_output(cells):

    return {

        "schema_version": "1.0",
        "source": "NASA_GPM_IMERG",
        "crs": EXPECTED_CRS,

        "region": {
            "code": "KA-BENGALURU-URBAN",
            "name": "Bengaluru Urban",
            "district": "Bengaluru Urban",
            "state": "Karnataka",
            "country": "India"
        },

        "data_date": DATA_DATE,
        "resolution_m": 1000,

        "indicator_metadata": create_metadata(),

        "cells": cells
    }


# ==========================================
# 9. SAVE JSON SAFELY
# ==========================================

def save_json(output, cells):

    print("\nSaving JSON files...")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    sample_output = output.copy()
    sample_output["cells"] = cells[:3]

    if len(sample_output["cells"]) != 3:
        raise ValueError("Unable to create three-cell sample.")

    for file, content in (
        (OUTPUT_FILE, output),
        (SAMPLE_FILE, sample_output)
    ):

        temporary_file = file.with_suffix(file.suffix + ".tmp")

        try:
            with temporary_file.open(
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    content,
                    f,
                    indent=2,
                    allow_nan=False
                )

            temporary_file.replace(file)

        except Exception:
            if temporary_file.exists():
                temporary_file.unlink()
            raise

        print("Saved:", file)
        print(
            "Size (MB):",
            round(file.stat().st_size / (1024 * 1024), 2)
        )


# ==========================================
# 10. MAIN PIPELINE
# ==========================================

def main():

    check_input_files()

    gdf = load_bengaluru_grid()

    gdf_geo, centroids = prepare_geometries(gdf)

    rainfall_values = load_rainfall(centroids)

    cells = build_cells(
        gdf_geo,
        centroids,
        rainfall_values
    )

    output = build_output(cells)

    save_json(output, cells)

    valid = sum(
        cell["indicators"]["rainfall_mm"] is not None
        for cell in cells
    )

    missing = len(cells) - valid

    print("\n========== EXPORT SUMMARY ==========")
    print("Region: Bengaluru Urban")
    print("Date:", DATA_DATE)
    print("Total cells:", len(cells))
    print("Valid rainfall:", valid)
    print("Missing rainfall:", missing)
    print("CRS:", EXPECTED_CRS)
    print("====================================")
    print("M2 export completed successfully!")


if __name__ == "__main__":
    main()
