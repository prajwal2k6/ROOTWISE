# ROOTWISE – M2 NASA Earth Observation Data Pipeline Documentation

## 1. Executive Summary & Objective

Milestone **M2 (NASA Earth Observation Data Processing, Geospatial Analytics, Indicator Integration, Quality Validation, and Dataset Export)** establishes the scientific and geospatial backbone of the ROOTWISE NASA Space Apps Hackathon platform.

The objective of M2 is to transform raw, multi-source NASA Earth Observation (EO) satellite measurements and global atmospheric assimilation reanalyses into a unified, high-resolution (1 km), scientifically validated, and standardized geospatial data layer for agricultural intelligence.

The operational pilot is implemented over **Bengaluru Urban District, Karnataka, India** (`KA-BENGALURU-URBAN`) for the target observation date **2016-01-01**, comprising **2,380 deterministic 1 km × 1 km grid cells**.

All seven target indicators are fully integrated, quality-screened, and validated:
1. `rainfall_mm` — NASA GPM IMERG V07B (Daily precipitation)
2. `temperature_min_c` — NASA POWER MERRA-2 (Daily minimum 2m temperature)
3. `temperature_max_c` — NASA POWER MERRA-2 (Daily maximum 2m temperature)
4. `humidity_pct` — NASA POWER MERRA-2 (Daily relative humidity)
5. `soil_moisture_pct` — NASA SMAP SPL3SMP V009 (Topsoil moisture fraction)
6. `ndvi` — NASA MODIS/Terra MOD13Q1 V061 (Vegetation index)
7. `evapotranspiration_mm` — NASA MODIS/Terra MOD16A2GF V061 (8-day accumulated ET)

---

## 2. Project Directory Structure

```text
ROOTWISE/
├── data/
│   ├── boundaries/
│   │   └── india_districts.geojson              # Raw Survey of India district boundaries
│   ├── processed/
│   │   ├── boundaries/
│   │   │   └── india_districts_cleaned.gpkg     # Cleaned, topology-checked administrative boundaries
│   │   └── gpm/
│   │       └── gpm_india_20160101.nc            # Cropped Indian sub-continent GPM NetCDF-4
│   ├── grids/
│   │   └── india/                               # National 1 km grid GeoParquet (36 States/UTs, 3.38M cells)
│   │       ├── KA.parquet                       # Karnataka statewide 1 km grid (192,204 cells)
│   │       └── ...
│   ├── raw/
│   │   ├── gpm/
│   │   │   └── 3B-DAY.MS.MRG.3IMERG.20160101-S000000-E235959.V07B.nc4
│   │   ├── smap/
│   │   │   └── SMAP_L3_SM_P_20160101_R19240_001.h5
│   │   └── modis/
│   │       ├── bengaluru_urban_boundary.geojson # Validated district vector for AppEEARS
│   │       ├── MOD13Q1.061__250m_16_days_NDVI_doy2016001000000_aid0001.tif
│   │       ├── MOD13Q1.061__250m_16_days_pixel_reliability_doy2016001000000_aid0001.tif
│   │       ├── MOD13Q1.061__250m_16_days_VI_Quality_doy2016001000000_aid0001.tif
│   │       ├── MOD16A2GF.061_ET_500m_doy2016001000000_aid0001.tif
│   │       └── MOD16A2GF.061_ET_QC_500m_doy2016001000000_aid0001.tif
│   └── outputs/
│       ├── bengaluru_urban_20160101.json         # Master production dataset (2,380 cells)
│       ├── bengaluru_urban_20160101.parquet      # Production GeoParquet export
│       ├── bengaluru_urban_20160101.geojson      # Production RFC 7946 GeoJSON export
│       ├── bengaluru_urban_sample_3_cells.json   # 3-cell verified sample dataset
│       ├── data_dictionary.json                  # Complete machine-readable data dictionary
│       └── final_validation_report.txt           # Automated certification audit report
├── docs/
│   ├── M2_data_pipeline.md                       # This pipeline documentation
│   ├── M2_M3_handoff.md                          # Production handoff specification for M3
│   └── modis_et_integration_plan.md              # Technical integration plan for MOD16A2GF
└── scripts/
    ├── clean_boundaries.py                       # Validates and cleans national district boundaries
    ├── create_india_grid.py                      # Generates nationwide 1 km grid in EPSG:7755
    ├── create_bengaluru_json.py                  # Initializes Bengaluru Urban pilot dataset with GPM
    ├── integrate_nasa_power.py                   # Integrates MERRA-2 daily climate variables
    ├── integrate_smap.py                         # Integrates SMAP radiometer soil moisture
    ├── integrate_modis_ndvi.py                   # Integrates MOD13Q1 NDVI with strict QA
    ├── integrate_modis_et.py                     # Integrates MOD16A2GF 8-day accumulated ET
    ├── inspect_modis_et_rasters.py               # Read-only diagnostic raster profiler
    ├── validate_bengaluru_json.py                # Comprehensive 7-indicator verification suite
    ├── export_bengaluru_geoparquet.py            # Converts master JSON to GeoParquet
    └── export_bengaluru_geojson.py               # Converts master JSON to GeoJSON
```

---

## 3. Geospatial Foundation: Boundaries, Grids & Coordinate Systems

### 3.1. Administrative Boundaries
- **Source**: Survey of India (SOI) official district boundary shapefiles.
- **Cleaning**: Topology verified, self-intersections repaired via `shapely.validation.make_valid`, multi-part geometries unified into valid `MultiPolygon`.
- Sourced district code `525` (`Bengaluru Urban`) with absolute spatial separation from district code `526` (`Bengaluru Rural`).

### 3.2. National 1 km Planar Processing Grid
- **Projected CRS**: **`EPSG:7755`** (India National Coordinate System - Lambert Conformal Conic / WGS84).
- **Grid Generation**: A uniform 1 km × 1 km regular planar mesh generated across India, clipped per state/UT boundary.
- **National Coverage**: 36 States/UTs, totaling **3,383,254 cells**.
- **Karnataka Tile (`KA.parquet`)**: 192,204 cells.
- **Bengaluru Urban Extraction**: Exactly **2,380 grid cells** intersect the Bengaluru Urban district polygon.
- **Grid ID Format**: Deterministic string `{state_code}_{district_code}_{x_m}_{y_m}` (e.g., `29_525_3710000_2796000`), anchoring each cell permanently to its EPSG:7755 coordinate origin.

### 3.3. Output Geometry Coordinate Reference System
- **Output CRS**: **`EPSG:4326`** (WGS84 latitude/longitude).
- Each cell polygon is reprojected from EPSG:7755 into EPSG:4326.
- All cell geometries are validated closed polygons with verified bounding ranges:
  - Longitude: `[77.3255° E, 77.8359° E]`
  - Latitude: `[12.6575° N, 13.2330° N]`

---

## 4. NASA Datasets, Products & Acquisition

| Indicator | NASA Mission / Source | Product Short Name | Collection / Version | Native Resolution | Temporal Span / Window |
|---|---|---|---|---|---|
| **Rainfall** | NASA GPM (Global Precipitation Measurement) | `3B-DAY.MS.MRG.3IMERG` | Version 07B | 0.1° (~11.1 km) | 2016-01-01 (Daily total) |
| **Air Temperature (Min)** | NASA POWER / MERRA-2 Assimilation | `T2M_MIN` | MERRA-2 | 0.5° × 0.625° (~55 km) | 2016-01-01 (Daily min) |
| **Air Temperature (Max)** | NASA POWER / MERRA-2 Assimilation | `T2M_MAX` | MERRA-2 | 0.5° × 0.625° (~55 km) | 2016-01-01 (Daily max) |
| **Relative Humidity** | NASA POWER / MERRA-2 Assimilation | `RH2M` | MERRA-2 | 0.5° × 0.625° (~55 km) | 2016-01-01 (Daily mean) |
| **Soil Moisture** | NASA SMAP (Soil Moisture Active Passive) | `SPL3SMP` | Version 009 | 36 km EASE-Grid 2.0 | 2016-01-01 (PM Ascending Pass ~12:22 UTC) |
| **NDVI** | NASA MODIS / Terra | `MOD13Q1` | Version 061 | 250 m Sinusoidal Grid | 2016-01-01 to 2016-01-16 (16-day composite) |
| **Evapotranspiration** | NASA MODIS / Terra | `MOD16A2GF` | Version 061 | 500 m Sinusoidal Grid | 2016-01-01 to 2016-01-08 (8-day composite) |

---

## 5. Indicator Integration & Scientific Quality Policy

### 5.1. Rainfall (`rainfall_mm`)
- **Native Product**: NASA GPM IMERG Final Run V07B daily liquid-equivalent accumulation.
- **Physical Range**: $\ge 0.0\text{ mm/day}$.
- **Method**: Area-weighted grid extraction.
- **Observations**: Winter dry day across south-interior Karnataka; all 2,380 cells recorded $0.00\text{ mm}$. True zero precipitation is strictly preserved as `0.0`.

### 5.2. Minimum & Maximum Temperature (`temperature_min_c`, `temperature_max_c`)
- **Native Product**: NASA POWER agroclimatology API, sourcing MERRA-2 atmospheric assimilation.
- **Method**: Nearest valid regional grid point assignment.
- **Observed Range**:
  - `temperature_min_c`: $12.77^\circ\text{C}$ to $13.75^\circ\text{C}$ (mean: $12.85^\circ\text{C}$)
  - `temperature_max_c`: $25.89^\circ\text{C}$ to $27.67^\circ\text{C}$ (mean: $27.12^\circ\text{C}$)

### 5.3. Relative Humidity (`humidity_pct`)
- **Native Product**: NASA POWER MERRA-2 2-metre relative humidity (`RH2M`).
- **Method**: Nearest valid regional grid point assignment.
- **Observed Range**: $73.06\%$ to $78.86\%$ (mean: $73.18\%$).

### 5.4. Topsoil Moisture (`soil_moisture_pct`)
- **Native Product**: NASA SMAP `SPL3SMP` Version 009 PM ascending pass (`soil_moisture_pm`).
- **Quality Mask**: `(retrieval_qual_flag_pm & 0b111) == 0`.
- **Physical Range**: $0.02$ to $0.50\text{ m}^3/\text{m}^3$, converted to percentage ($\times 100$).
- **Method**: Nearest valid quality-filtered SMAP pixel. Central urban core pixels failed quality tests due to radio-frequency interference and impervious surfaces; cells are mapped to five surrounding peri-urban/rural pixels (max distance: $37.91\text{ km}$).
- **Observed Range**: $8.55\%$ to $13.32\%$ (mean: $10.33\%$).

### 5.5. Vegetation Index (`ndvi`)
- **Native Product**: NASA MODIS `MOD13Q1.061` 250 m 16-day composite (`250m 16 days NDVI`).
- **Quality Mask**: Strict dual-layer filter:
  `pixel_reliability == 0` (Good Data) $\land$ `(VI_Quality & 0b11) == 0` (Good Quality) $\land$ `raw != -3000`.
- **Spatial Assignment**:
  1. Centroid point sampling: $877$ cells ($36.85\%$).
  2. Within-cell polygon fallback (mean of valid interior 250m pixels): $416$ cells ($17.48\%$).
  3. Null preservation (zero valid pixels inside cell): **$1,087$ cells ($45.67\%$)**.
- **Observed Range**: $-0.1219$ to $+0.7782$ (mean: $+0.4142$).
- **Scientific Rule**: Urban core cells affected by dense built-up interference and high aerosols remain strictly `null`. Null values represent retrieval uncertainty, NOT zero vegetation.

### 5.6. Evapotranspiration (`evapotranspiration_mm`)
- **Native Product**: NASA MODIS `MOD16A2GF.061` 500 m 8-day composite (`ET_500m`).
- **Temporal Nature**: **8-day accumulated total ($\text{mm/8day}$)** covering `2016-01-01` to `2016-01-08`. To obtain the daily average rate ($\text{mm/day}$), divide by $8$ (`daily_rate_divisor: 8`).
- **Valid Range**: Documented raw range `[-32767, 32700]`, scale factor `0.1`.
- **Special Fill Codes**:
  `32761` (unclassified), `32762` (urban/built-up), `32763` (wetland), `32764` (snow), `32765` (barren), `32766` (water), `32767` (fill) $\to$ **all strictly excluded and preserved as `null`**.
- **Spatial Assignment**:
  1. Centroid point sampling: **$2,067$ cells ($86.85\%$)**.
  2. Within-cell polygon fallback (mean of valid interior 500m pixels): **$104$ cells ($4.37\%$)**.
  3. Total populated: **$2,171$ cells ($91.22\%$)**.
  4. Null preservation (unmodeled urban/water): **$209$ cells ($8.78\%$)**.
- **Observed Range**:
  - 8-day accumulated ET: **$3.80$ to $22.40\text{ mm/8day}$** (mean: $6.92\text{ mm/8day}$)
  - Daily equivalent: **$0.475$ to $2.800\text{ mm/day}$** (mean: $0.865\text{ mm/day}$)

---

## 6. Summary Indicator Coverage Table

| Indicator | Field Name | Source Product | Populated Cells | Null Cells | Coverage % | Observed Range | Units |
|---|---|---|---|---|---|---|---|
| **Rainfall** | `rainfall_mm` | NASA GPM IMERG V07B | 2,380 | 0 | 100.00% | `0.00` | `mm/day` |
| **Min Temperature** | `temperature_min_c` | NASA POWER MERRA-2 | 2,380 | 0 | 100.00% | `[12.77, 13.75]` | `°C` |
| **Max Temperature** | `temperature_max_c` | NASA POWER MERRA-2 | 2,380 | 0 | 100.00% | `[25.89, 27.67]` | `°C` |
| **Humidity** | `humidity_pct` | NASA POWER MERRA-2 | 2,380 | 0 | 100.00% | `[73.06, 78.86]` | `%` |
| **Soil Moisture** | `soil_moisture_pct` | NASA SMAP PM V009 | 2,380 | 0 | 100.00% | `[8.55, 13.32]` | `%` |
| **Vegetation Index** | `ndvi` | NASA MODIS MOD13Q1.061 | 1,293 | 1,087 | 54.33% | `[-0.12, 0.78]` | dimensionless |
| **Evapotranspiration** | `evapotranspiration_mm` | NASA MODIS MOD16A2GF.061 | 2,171 | 209 | 91.22% | `[3.80, 22.40]` | `mm/8day` |

---

## 7. Deliverables & Production Output Files

1. **Master Output JSON**:
   `data/outputs/bengaluru_urban_20160101.json` (`2.76 MB`)
   - Schema version `1.0`, CRS `EPSG:4326`, 2,380 cells, full metadata.
2. **GeoParquet File**:
   `data/outputs/bengaluru_urban_20160101.parquet` (`221.95 KB`)
   - Snappy compressed, includes GeoPandas/PyArrow geometry metadata and embedded schema metadata.
3. **GeoJSON File**:
   `data/outputs/bengaluru_urban_20160101.geojson` (`3.18 MB`)
   - RFC 7946 compliant FeatureCollection of 2,380 features.
4. **Sample Verification JSON**:
   `data/outputs/bengaluru_urban_sample_3_cells.json` (`10.35 KB`)
   - First 3 cells with identical metadata for rapid API unit testing.
5. **Data Dictionary**:
   `data/outputs/data_dictionary.json` (`11.45 KB`)
   - Comprehensive machine-readable indicator catalog.
6. **Certification Report**:
   `data/outputs/final_validation_report.txt` (`4.12 KB`)
   - Automated audit report certifying 100% test pass.

---

## 8. Reproducibility & Pipeline Execution Instructions

To reproduce the entire M2 processing sequence from raw data to exports:

```powershell
# 1. Clean administrative boundaries
python scripts/clean_boundaries.py

# 2. Build nationwide and Karnataka 1 km processing grids
python scripts/create_india_grid.py

# 3. Initialize Bengaluru Urban dataset with GPM rainfall
python scripts/create_bengaluru_json.py

# 4. Integrate NASA POWER climate variables (temperature min/max, humidity)
python scripts/integrate_nasa_power.py

# 5. Integrate NASA SMAP soil moisture
python scripts/integrate_smap.py

# 6. Integrate NASA MODIS NDVI
python scripts/integrate_modis_ndvi.py

# 7. Integrate NASA MODIS Evapotranspiration
python scripts/integrate_modis_et.py

# 8. Execute final validation suite
python scripts/validate_bengaluru_json.py

# 9. Export production GeoParquet and GeoJSON
python scripts/export_bengaluru_geoparquet.py
python scripts/export_bengaluru_geojson.py
```
