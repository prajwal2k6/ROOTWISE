# ROOTWISE M2 to M3 Integration Handoff Specification

## 1. Handoff Purpose & Status
This document provides the definitive technical interface specification for **Milestone M3 (Backend API, Database Ingestion, and Model Serving)** to ingest, store, and serve the validated Earth Observation datasets produced by **Milestone M2**.

> [!NOTE]
> M2 data processing, quality filtering, spatial alignment, and export certification are **100% complete**. No M3 database tables, ingestion scripts, or API routes have been implemented yet; this document provides everything M3 requires to implement ingestion cleanly.

---

## 2. Production Dataset Locations & Formats

All production deliverables are located under [`data/outputs/`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/outputs/):

| File Path | Format | Size | Description | Primary Target Consumer |
|---|---|---|---|---|
| [`data/outputs/bengaluru_urban_20160101.json`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/outputs/bengaluru_urban_20160101.json) | JSON (Schema 1.0) | `2.76 MB` | Master dataset containing batch metadata, full indicator descriptions, and 2,380 cell objects | Document stores, NoSQL, direct JSON ingestion |
| [`data/outputs/bengaluru_urban_20160101.parquet`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/outputs/bengaluru_urban_20160101.parquet) | GeoParquet (Snappy) | `221.95 KB` | Columnar table with PyArrow/GeoPandas geometry metadata and embedded table schema | DuckDB, PostGIS / PostgreSQL, Polars, Pandas |
| [`data/outputs/bengaluru_urban_20160101.geojson`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/outputs/bengaluru_urban_20160101.geojson) | GeoJSON FeatureCollection | `3.18 MB` | RFC 7946 compliant vector feature collection (2,380 features) | Mapbox, Leaflet, GIS clients, Vector tile pipelines |
| [`data/outputs/bengaluru_urban_sample_3_cells.json`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/outputs/bengaluru_urban_sample_3_cells.json) | JSON (Schema 1.0) | `10.35 KB` | First 3 cells with identical metadata structure | Fast unit testing, CI/CD validation |
| [`data/outputs/data_dictionary.json`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/outputs/data_dictionary.json) | JSON | `11.45 KB` | Machine-readable data dictionary documenting all fields, units, and limitations | API documentation, Swagger/OpenAPI generators |
| [`data/outputs/final_validation_report.txt`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/outputs/final_validation_report.txt) | Plain Text | `4.12 KB` | Audit certification report with exact check results | QA sign-off & compliance verification |

---

## 3. Geospatial Specifications & Schema

* **Target Region**: Bengaluru Urban District (`KA-BENGALURU-URBAN`), Karnataka, India.
* **Observation Date**: `2016-01-01`
* **Total Grid Cells**: Exactly **`2,380`** unique 1 km × 1 km cells.
* **Coordinate Reference System (CRS)**: **`EPSG:4326`** (WGS84 latitude/longitude).
* **Geometry Format**: GeoJSON `Polygon` with outer ring coordinate pairs `[lon, lat]`.
* **Grid ID Pattern**: Deterministic string `{state_code}_{district_code}_{x_m}_{y_m}` anchored to the Survey of India national projected planar grid (EPSG:7755).
  * Example: `"29_525_3710000_2796000"` (`29` = Karnataka, `525` = Bengaluru Urban).

---

## 4. Indicator Definitions, Units & Semantics

| Indicator Field Name | Data Type | Units | Populated Count | Null Count | Coverage % | Semantic Meaning of Value |
|---|---|---|---|---|---|---|
| `rainfall_mm` | `float` / `null` | `mm/day` | 2,380 | 0 | 100.0% | Daily liquid-equivalent precipitation. `0.0` represents a verified dry day, not missing data. |
| `temperature_min_c` | `float` / `null` | `°C` | 2,380 | 0 | 100.0% | Daily minimum surface air temperature (2m). |
| `temperature_max_c` | `float` / `null` | `°C` | 2,380 | 0 | 100.0% | Daily maximum surface air temperature (2m). |
| `humidity_pct` | `float` / `null` | `%` | 2,380 | 0 | 100.0% | Daily mean relative humidity (2m). |
| `soil_moisture_pct` | `float` / `null` | `%` | 2,380 | 0 | 100.0% | Topsoil volumetric water content (0–5 cm depth), percentage fraction ($0\text{--}100\%$). |
| `ndvi` | `float` / `null` | dimensionless | 1,293 | 1,087 | 54.33% | Normalized Difference Vegetation Index ($-0.20$ to $+1.00$). High values indicate dense canopy; near-zero indicates bare soil/built surfaces. |
| `evapotranspiration_mm` | `float` / `null` | `mm/8day` | 2,171 | 209 | 91.22% | **8-day accumulated total evapotranspiration** (Jan 1 to Jan 8, 2016). To compute mean daily rate ($\text{mm/day}$), divide by $8$. |

### Critical Missing-Value Semantics for M3:
* **JSON Null vs. Zero**: A value of `null` indicates that the satellite sensor or algorithm was unable to retrieve a physically valid measurement over that surface (e.g. dense urban impervious core, cloud/aerosol interference, or water body). **M3 MUST NOT substitute `0.0` for `null`**.
* In `ndvi`, `null` means unmeasured/cloud/aerosol/urban-interference, NOT zero vegetation.
* In `evapotranspiration_mm`, `null` indicates that the Penman-Monteith algorithm does not model impervious urban built-up surfaces (Code `32762`); substituting `0.0` would falsely imply zero transpiration on a vegetated surface.

---

## 5. Master JSON Structure Example

Each cell object in `data/outputs/bengaluru_urban_20160101.json` conforms to the following structure:

```json
{
  "grid_id": "29_525_3710000_2796000",
  "state": "Karnataka",
  "district": "Bengaluru Urban",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [77.33203576052576, 12.95775002490972],
        [77.33212837162063, 12.95295372627129],
        [77.33186216503911, 12.953383298146576],
        [77.33108140906037, 12.955535828382585],
        [77.33203576052576, 12.95775002490972]
      ]
    ]
  },
  "centroid_lat": 12.95535,
  "centroid_lon": 77.33155,
  "indicators": {
    "rainfall_mm": 0.0,
    "soil_moisture_pct": 13.3201,
    "temperature_min_c": 12.77,
    "temperature_max_c": 27.08,
    "humidity_pct": 73.06,
    "ndvi": 0.465,
    "evapotranspiration_mm": 6.8
  },
  "data_quality": "estimated"
}
```

---

## 6. Recommended Ingestion Patterns for M3

### Option A: Ingestion into PostgreSQL / PostGIS (Recommended for Relational & Spatial Queries)
Using GeoPandas or psycopg3 with the GeoParquet export:
```python
import geopandas as gpd
from sqlalchemy import create_engine

# Read GeoParquet
gdf = gpd.read_parquet("data/outputs/bengaluru_urban_20160101.parquet")

# Ingest directly into PostGIS
engine = create_engine("postgresql://user:password@localhost:5432/rootwise_db")
gdf.to_postgis("bengaluru_urban_cells", engine, if_exists="replace", index=False)
```

### Option B: Ingestion into DuckDB (Fastest Analytical Queries)
```sql
INSTALL spatial;
LOAD spatial;

CREATE TABLE cells AS
SELECT * FROM read_parquet('data/outputs/bengaluru_urban_20160101.parquet');

-- Fast spatial centroid query
SELECT grid_id, rainfall_mm, ndvi, evapotranspiration_mm
FROM cells
WHERE evapotranspiration_mm IS NOT NULL;
```

### Option C: FastAPI / Backend Endpoint Serving
For serving via a FastAPI router in M3:
```python
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

app = FastAPI(title="ROOTWISE API")

DATA_FILE = Path("data/outputs/bengaluru_urban_20160101.json")
with DATA_FILE.open("r", encoding="utf-8") as f:
    DATASET = json.load(f)
CELLS_BY_ID = {c["grid_id"]: c for c in DATASET["cells"]}

@app.get("/api/v1/grid/{grid_id}")
def get_grid_cell(grid_id: str):
    if grid_id not in CELLS_BY_ID:
        raise HTTPException(status_code=404, detail="Grid cell not found")
    return CELLS_BY_ID[grid_id]
```

---

## 7. Known Scientific Limitations to Expose to End Users
1. **Spatial Footprints**: Data originates from satellite sensors and reanalysis assimilation with footprints ranging from 250 m (MODIS NDVI) to ~55 km (NASA POWER). Resampling to 1 km provides a uniform indexing framework, but individual cells in coarse products share regional background values.
2. **SMAP Soil Moisture**: Mapped to 5 surrounding peri-urban/rural pixels due to central urban radio-frequency interference and impervious surfaces. Maximum distance to source pixel is 37.91 km.
3. **Evapotranspiration Composite**: Represents an 8-day accumulated integral ($\text{mm/8day}$). Divide by 8 for daily average rate; do not confuse with instantaneous daily flux.
