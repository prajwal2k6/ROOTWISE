
from pathlib import Path
import json

import geopandas as gpd
import numpy as np
import xarray as xr
from shapely.geometry import mapping

# ==========================================
# 1. INPUT AND OUTPUT FILES
# ==========================================

grid_file = Path(
    "data/grids/india/Karnataka_1km_grid.parquet"
)

gpm_file = Path(
    "data/raw/gpm/3B-DAY.MS.MRG.3IMERG.20160101-S000000-E235959.V07B.nc4"
)


output_file = Path(
    "data/outputs/bengaluru_urban_20160101.json"
)

sample_file = Path(
    "data/outputs/bengaluru_urban_sample_3_cells.json"
)

DATA_DATE = "2016-01-01"

# ==========================================
# 2. CHECK INPUT FILES
# ==========================================

print("Checking input files...")

if not grid_file.exists():
    raise FileNotFoundError(f"Grid file not found: {grid_file}")

if not gpm_file.exists():
    raise FileNotFoundError(f"GPM file not found: {gpm_file}")

# ==========================================
# 3. LOAD BENGALURU URBAN GRID
# ==========================================

print("\nLoading Karnataka grid...")

gdf = gpd.read_parquet(grid_file)

gdf = gdf[
    gdf["district"].str.strip().str.casefold()
    == "bengaluru urban"
].copy()

if gdf.empty:
    raise ValueError("Bengaluru Urban grid cells not found.")

print("Bengaluru Urban cells:", len(gdf))

# Check grid IDs
if gdf["grid_id"].isna().any():
    raise ValueError("Some grid IDs are missing.")

if gdf["grid_id"].duplicated().any():
    raise ValueError("Duplicate grid IDs found.")

# ==========================================
# 4. CONVERT TO EPSG:4326
# ==========================================

print("\nConverting geometries to EPSG:4326...")

gdf_geo = gdf.to_crs("EPSG:4326")

# Calculate centroids in original projected CRS
# before transforming them to longitude/latitude.

centroids = gpd.GeoSeries(
    gdf.geometry.centroid,
    crs=gdf.crs
).to_crs("EPSG:4326")

# ==========================================
# 5. LOAD NASA GPM DATA
# ==========================================

print("\nLoading NASA GPM rainfall data...")

ds = xr.open_dataset(
    gpm_file,
    engine="netcdf4"
)

try:
    if "precipitation" not in ds:
        raise ValueError(
            "GPM precipitation variable not found."
        )

    rain = ds["precipitation"].isel(time=0)

    print("GPM dimensions:", rain.dims)
    print(
        "GPM units:",
        rain.attrs.get("units", "Not specified")
    )

    # ==========================================
    # 6. MATCH RAINFALL TO GRID CENTROIDS
    # ==========================================

    print("\nMatching GPM rainfall to grid cells...")

    latitudes = centroids.y.to_numpy()
    longitudes = centroids.x.to_numpy()

    lat_points = xr.DataArray(
        latitudes,
        dims="cell"
    )

    lon_points = xr.DataArray(
        longitudes,
        dims="cell"
    )

    # Nearest GPM pixel sampling.
    # GPM native resolution is approximately 0.1 degree.

    sampled = rain.sel(
        lon=lon_points,
        lat=lat_points,
        method="nearest"
    )

    rainfall_values = sampled.values

    # ==========================================
    # 7. BUILD CELL DATA
    # ==========================================

    print("\nBuilding M3 JSON output...")

    cells = []

    for i, (_, row) in enumerate(gdf_geo.iterrows()):

        value = rainfall_values[i]

        if np.isfinite(value):
            rainfall = round(float(value), 4)
            quality = "estimated"
        else:
            rainfall = None
            quality = "missing"

        centroid = centroids.iloc[i]

        cell = {
            "grid_id": str(row["grid_id"]),

            "state": str(row["state_name"]),

            "district": str(row["district"]),

            "geometry": mapping(row.geometry),

            "centroid_lat": round(
                float(centroid.y), 6
            ),

            "centroid_lon": round(
                float(centroid.x), 6
            ),

            "indicators": {
                "rainfall_mm": rainfall,
                "soil_moisture_pct": None,
                "temperature_min_c": None,
                "temperature_max_c": None,
                "humidity_pct": None,
                "ndvi": None,
                "evapotranspiration_mm": None
            },

            "data_quality": quality
        }

        cells.append(cell)

finally:
    ds.close()

# ==========================================
# 8. INDICATOR METADATA
# ==========================================

indicator_metadata = {

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
# 9. BUILD FINAL M3 JSON BATCH
# ==========================================

output = {

    "schema_version": "1.0",

    "source": "NASA_GPM_IMERG",

    "crs": "EPSG:4326",

    "region": {
        "code": "KA-BENGALURU-URBAN",
        "name": "Bengaluru Urban",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "country": "India"
    },

    "data_date": DATA_DATE,

    "resolution_m": 1000,

    "indicator_metadata": indicator_metadata,

    "cells": cells
}

# ==========================================
# 10. SAVE COMPLETE JSON
# ==========================================

print("\nSaving complete JSON...")

output_file.parent.mkdir(
    parents=True,
    exist_ok=True
)

with output_file.open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=2,
        allow_nan=False
    )

# ==========================================
# 11. CREATE THREE-CELL SAMPLE
# ==========================================

print("\nCreating three-cell sample...")

sample_output = output.copy()

sample_output["cells"] = cells[:3]

with sample_file.open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        sample_output,
        f,
        indent=2,
        allow_nan=False
    )

# ==========================================
# 12. FINAL SUMMARY
# ==========================================

valid_rainfall = sum(
    cell["indicators"]["rainfall_mm"] is not None
    for cell in cells
)

missing_rainfall = len(cells) - valid_rainfall

print("\n========== EXPORT COMPLETED ==========")

print("Region: Bengaluru Urban")
print("Observation date:", DATA_DATE)

print("Total grid cells:", len(cells))

print("Cells with rainfall:", valid_rainfall)

print("Cells with missing rainfall:", missing_rainfall)

print("Unique grid IDs:", len({
    cell["grid_id"] for cell in cells
}))

print("CRS: EPSG:4326")

print("Full JSON:", output_file)

print(
    "Full JSON size (MB):",
    round(
        output_file.stat().st_size / (1024 * 1024),
        2
    )
)

print("Sample JSON:", sample_file)

print("Sample cells:", len(sample_output["cells"]))

print("\nM2 JSON export completed successfully!")
