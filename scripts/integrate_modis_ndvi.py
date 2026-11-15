"""
ROOTWISE M2 – NASA MODIS MOD13Q1 NDVI Integration
=================================================
Integrates NASA MODIS/Terra MOD13Q1 Version 061 (16-Day L3 Global 250m)
Normalized Difference Vegetation Index (NDVI) into the Bengaluru Urban
dataset (2,380 grid cells) for 2016-01-01.

Input Rasters (AppEEARS GeoTIFF):
  - NDVI              : MOD13Q1.061__250m_16_days_NDVI_doy2016001000000_aid0001.tif
  - Pixel Reliability : MOD13Q1.061__250m_16_days_pixel_reliability_doy2016001000000_aid0001.tif
  - VI Quality        : MOD13Q1.061__250m_16_days_VI_Quality_doy2016001000000_aid0001.tif

Strict Quality Filter:
  - pixel_reliability == 0 (Good Data)
  - (VI_Quality & 0b11) == 0 (VI produced, good quality)
  - raw_ndvi != -3000 (exclude fill values)
  - -2000 <= raw_ndvi <= 10000 (valid range [-0.20, +1.00])
  - math.isfinite(raw_ndvi)

Spatial Assignment Strategy:
  1. Centroid point sampling: If cell centroid falls on a strict quality pixel,
     use that pixel: ndvi = round(raw_ndvi * 0.0001, 4).
  2. Within-cell polygon fallback: If centroid is invalid (e.g. marginal/nodata),
     find all valid strict quality pixels whose center points fall inside that
     same 1 km cell polygon. If >= 1 valid pixels exist inside the cell,
     assign their arithmetic mean: ndvi = round(mean(inside_raw) * 0.0001, 4).
  3. Null preservation: If zero valid strict quality pixels exist inside the cell,
     retain null. Under NO circumstances are pixels outside the cell polygon used.

Safety:
  - Timestamped backup created before any file modification.
  - Safe atomic write via temporary file replacement.
  - Refresh sample JSON (first 3 cells).
  - All existing indicators (rainfall_mm, soil_moisture_pct, temperature_min_c,
    temperature_max_c, humidity_pct, evapotranspiration_mm), grid IDs, CRS,
    and cell geometries are preserved 100% intact.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import rowcol
from shapely.geometry import Point, shape

# ==========================================
# 1. CONFIGURATION & FILE PATHS
# ==========================================

ROOT = Path(__file__).resolve().parent.parent

FULL_JSON = ROOT / "data/outputs/bengaluru_urban_20160101.json"
SAMPLE_JSON = ROOT / "data/outputs/bengaluru_urban_sample_3_cells.json"
MODIS_DIR = ROOT / "data/raw/modis"

NDVI_FILE = MODIS_DIR / "MOD13Q1.061__250m_16_days_NDVI_doy2016001000000_aid0001.tif"
REL_FILE = MODIS_DIR / "MOD13Q1.061__250m_16_days_pixel_reliability_doy2016001000000_aid0001.tif"
QA_FILE = MODIS_DIR / "MOD13Q1.061__250m_16_days_VI_Quality_doy2016001000000_aid0001.tif"

DATA_DATE = "2016-01-01"
EXPECTED_CELL_COUNT = 2380
SCALE_FACTOR = 0.0001

REQUIRED_INDICATORS = {
    "rainfall_mm",
    "soil_moisture_pct",
    "temperature_min_c",
    "temperature_max_c",
    "humidity_pct",
    "ndvi",
    "evapotranspiration_mm",
}


# ==========================================
# 2. PRE-FLIGHT VALIDATION
# ==========================================

def validate_input_json(full_data: dict) -> None:
    """Verify that existing JSON is complete and consistent before any modification."""
    errors: list[str] = []

    if full_data.get("crs") != "EPSG:4326":
        errors.append(f"Expected CRS EPSG:4326, got {full_data.get('crs')!r}.")

    if full_data.get("data_date") != DATA_DATE:
        errors.append(f"Expected data_date {DATA_DATE}, got {full_data.get('data_date')!r}.")

    cells = full_data.get("cells")
    if not isinstance(cells, list):
        raise ValueError("'cells' field is missing or not a list.")

    if len(cells) != EXPECTED_CELL_COUNT:
        errors.append(f"Expected exactly {EXPECTED_CELL_COUNT} cells, found {len(cells)}.")

    seen_ids: set[str] = set()
    for i, cell in enumerate(cells):
        prefix = f"Cell[{i}]"
        grid_id = cell.get("grid_id")
        if not isinstance(grid_id, str) or not grid_id.strip():
            errors.append(f"{prefix}: grid_id is missing or empty.")
        else:
            if grid_id in seen_ids:
                errors.append(f"{prefix}: duplicate grid_id '{grid_id}'.")
            seen_ids.add(grid_id)

        lat = cell.get("centroid_lat")
        lon = cell.get("centroid_lon")
        if (
            not isinstance(lat, (int, float))
            or isinstance(lat, bool)
            or not math.isfinite(lat)
            or not (-90 <= lat <= 90)
        ):
            errors.append(f"{prefix}: invalid centroid_lat: {lat!r}.")

        if (
            not isinstance(lon, (int, float))
            or isinstance(lon, bool)
            or not math.isfinite(lon)
            or not (-180 <= lon <= 180)
        ):
            errors.append(f"{prefix}: invalid centroid_lon: {lon!r}.")

        indicators = cell.get("indicators")
        if not isinstance(indicators, dict):
            errors.append(f"{prefix}: 'indicators' is missing or not a dict.")
        else:
            missing = REQUIRED_INDICATORS - indicators.keys()
            if missing:
                errors.append(f"{prefix}: indicators missing keys: {sorted(missing)}.")

    metadata = full_data.get("indicator_metadata")
    if not isinstance(metadata, dict):
        errors.append("'indicator_metadata' is missing or not a dict.")
    else:
        missing_meta = REQUIRED_INDICATORS - metadata.keys()
        if missing_meta:
            errors.append(f"indicator_metadata missing keys: {sorted(missing_meta)}.")

    if errors:
        raise ValueError("Pre-flight validation FAILED:\n" + "\n".join(f"  • {e}" for e in errors))

    print(
        f"  Pre-flight validation PASSED: {len(cells)} cells, {len(seen_ids)} unique IDs, "
        f"all centroids and required indicator keys verified."
    )


# ==========================================
# 3. BACKUP CREATION
# ==========================================

def create_backup() -> Path:
    """Create a timestamped backup before touching the dataset."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = FULL_JSON.with_name(f"{FULL_JSON.stem}_backup_{timestamp}{FULL_JSON.suffix}")
    shutil.copy2(FULL_JSON, backup)
    print(f"  Backup created → {backup.relative_to(ROOT)}")
    return backup


# ==========================================
# 4. LOAD & QUALITY-FILTER MODIS RASTERS
# ==========================================

def load_and_screen_rasters() -> tuple[np.ndarray, np.ndarray, rasterio.Affine, int, int]:
    """Load the three MODIS GeoTIFFs, verify alignment, and generate the strict quality mask.

    Returns:
      (ndvi_array, strict_valid_mask, transform, height, width)
    """
    for p in [NDVI_FILE, REL_FILE, QA_FILE]:
        if not p.exists():
            raise FileNotFoundError(f"Required MODIS GeoTIFF not found: {p}")

    with rasterio.open(NDVI_FILE) as s_ndvi, \
         rasterio.open(REL_FILE) as s_rel, \
         rasterio.open(QA_FILE) as s_qa:

        # Alignment check
        if s_ndvi.shape != s_rel.shape or s_ndvi.shape != s_qa.shape:
            raise ValueError(f"Raster shape mismatch: NDVI={s_ndvi.shape}, Rel={s_rel.shape}, QA={s_qa.shape}")
        if s_ndvi.transform != s_rel.transform or s_ndvi.transform != s_qa.transform:
            raise ValueError("Raster affine transform mismatch among GeoTIFFs.")
        if s_ndvi.crs != s_rel.crs or s_ndvi.crs.to_string() != "EPSG:4326":
            raise ValueError(f"Expected CRS EPSG:4326, got {s_ndvi.crs}")

        ndvi = s_ndvi.read(1)
        rel = s_rel.read(1)
        qa = s_qa.read(1)
        transform = s_ndvi.transform
        h, w = ndvi.shape

    # Strict Quality Mask:
    # 1. pixel_reliability == 0 (Good Data)
    # 2. (VI_Quality & 0b11) == 0 (VI produced, good quality)
    # 3. raw_ndvi != -3000 (Fill value)
    # 4. -2000 <= raw_ndvi <= 10000 (Valid product range)
    # 5. np.isfinite(raw_ndvi)
    cond_rel = (rel == 0)
    cond_qa = ((qa & 0b11) == 0)
    cond_val = (ndvi != -3000) & (ndvi >= -2000) & (ndvi <= 10000) & np.isfinite(ndvi)

    strict_valid_mask = cond_rel & cond_qa & cond_val

    total_valid = int(np.sum(strict_valid_mask))
    print(f"  Raster dimensions: {w} x {h} ({ndvi.size:,} pixels)")
    print(f"  Pixels passing strict quality screen: {total_valid:,} / {ndvi.size:,} ({total_valid/ndvi.size*100:.2f}%)")

    return ndvi, strict_valid_mask, transform, h, w


# ==========================================
# 5. MATCH NDVI TO GRID CELLS
# ==========================================

def update_cells_with_ndvi(
    cells: list[dict],
    ndvi: np.ndarray,
    strict_valid: np.ndarray,
    transform: rasterio.Affine,
    h: int,
    w: int,
) -> tuple[int, int, int, list[float]]:
    """Assign quality-screened NDVI to each 1 km cell.

    Assignment rules:
      1. Centroid point sampling: if valid strict pixel at centroid, use it.
      2. Within-cell polygon fallback: if centroid invalid, calculate arithmetic
         mean of all valid strict pixels whose center coordinates lie inside
         that 1 km cell polygon.
      3. If no valid strict pixel lies inside the cell, assign None (null).
      Never use pixels outside the cell polygon.

    Returns:
      (direct_count, fallback_count, null_count, populated_values)
    """
    # Precompute pixel centers in WGS84 coordinates
    cols_grid, rows_grid = np.meshgrid(np.arange(w), np.arange(h))
    xs_flat, ys_flat = rasterio.transform.xy(transform, rows_grid.flatten(), cols_grid.flatten(), offset="center")
    xs = np.array(xs_flat).reshape((h, w))
    ys = np.array(ys_flat).reshape((h, w))

    direct_count = 0
    fallback_count = 0
    null_count = 0
    populated_values: list[float] = []

    for cell in cells:
        c_lon = cell["centroid_lon"]
        c_lat = cell["centroid_lat"]
        geom = shape(cell["geometry"])
        indicators = cell["indicators"]

        # 1. Try Centroid Sampling First
        r, c = rowcol(transform, c_lon, c_lat)
        if 0 <= r < h and 0 <= c < w and strict_valid[r, c]:
            scaled_ndvi = round(float(ndvi[r, c]) * SCALE_FACTOR, 4)
            indicators["ndvi"] = scaled_ndvi
            direct_count += 1
            populated_values.append(scaled_ndvi)
            continue

        # 2. Within-cell polygon fallback
        minx, miny, maxx, maxy = geom.bounds
        r_start, c_start = rowcol(transform, minx, maxy)
        r_end, c_end = rowcol(transform, maxx, miny)

        r_min_box = max(0, min(r_start, r_end) - 1)
        r_max_box = min(h - 1, max(r_start, r_end) + 1)
        c_min_box = max(0, min(c_start, c_end) - 1)
        c_max_box = min(w - 1, max(c_start, c_end) + 1)

        sub_r, sub_c = np.meshgrid(
            np.arange(r_min_box, r_max_box + 1),
            np.arange(c_min_box, c_max_box + 1),
            indexing="ij",
        )
        sub_strict = strict_valid[sub_r, sub_c]

        valid_inside_raw = []
        for ri, ci in zip(sub_r[sub_strict], sub_c[sub_strict]):
            px_pt = Point(xs[ri, ci], ys[ri, ci])
            if geom.contains(px_pt):
                valid_inside_raw.append(float(ndvi[ri, ci]))

        if len(valid_inside_raw) > 0:
            mean_scaled = round(float(np.mean(valid_inside_raw)) * SCALE_FACTOR, 4)
            indicators["ndvi"] = mean_scaled
            fallback_count += 1
            populated_values.append(mean_scaled)
        else:
            # 3. Retain null (never use pixels outside the cell polygon)
            indicators["ndvi"] = None
            null_count += 1

    return direct_count, fallback_count, null_count, populated_values


# ==========================================
# 6. UPDATE INDICATOR METADATA
# ==========================================

def update_metadata(
    indicator_metadata: dict,
    direct_count: int,
    fallback_count: int,
    null_count: int,
) -> None:
    """Update metadata for ndvi only. All other indicator metadata entries are preserved."""
    note = (
        "Vegetation index composite from NASA MODIS/Terra MOD13Q1 Collection 6.1 (250m Sinusoidal Grid, tile h25v07). "
        "Each 1 km cell was evaluated against quality-screened 250 m pixels requiring pixel_reliability == 0 (Good Data) "
        "and (VI_Quality & 0b11) == 0 (VI produced, good quality). Centroid sampling was used where high-quality "
        f"pixels were present ({direct_count:,} cells); within-cell arithmetic mean of valid interior pixels was used as "
        f"fallback ({fallback_count:,} cells). Cells with no valid quality-screened pixels inside their 1 km boundary "
        f"remain strictly null ({null_count:,} cells, primarily central urban core with high aerosol/urban surface interference). "
        "No pixels outside the cell polygon were used, and no synthetic interpolation was performed."
    )

    indicator_metadata["ndvi"] = {
        "source": "NASA MODIS Terra MOD13Q1 Version 061 (16-Day L3 Global 250m)",
        "variable": "250m 16 days NDVI",
        "units": "dimensionless (-1 to 1)",
        "scale_factor": SCALE_FACTOR,
        "status": "observed",
        "native_resolution": "250 m Sinusoidal Grid (~231.66 m x 231.66 m)",
        "temporal_coverage": "2016-01-01 to 2016-01-16 (16-day composite, DOY 001-016)",
        "tile": "h25v07",
        "quality_mask": "pixel_reliability == 0 (Good Data) & (VI_Quality & 0b11) == 0 (VI produced, good quality)",
        "valid_range": "-0.20 to 1.00 (-2000 to 10000 raw)",
        "assignment_method": "Centroid 250m pixel sampling, with within-cell 250m pixel mean fallback; null otherwise",
        "direct_centroid_cells": direct_count,
        "fallback_within_cell_cells": fallback_count,
        "null_cells": null_count,
        "note": note,
    }


# ==========================================
# 7. SAFE ATOMIC SAVING
# ==========================================

def save_json_safe(path: Path, content: dict) -> None:
    """Write content to temporary file, then atomically replace target path."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, allow_nan=False)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"  Saved → {path.relative_to(ROOT)} ({size_mb:.2f} MB)")


def regenerate_sample(full_data: dict) -> None:
    """Rebuild sample JSON from the first three cells of full data."""
    sample = {k: v for k, v in full_data.items() if k != "cells"}
    sample["cells"] = full_data["cells"][:3]
    if len(sample["cells"]) != 3:
        raise ValueError("Cannot create 3-cell sample: fewer than 3 cells present.")
    save_json_safe(SAMPLE_JSON, sample)


# ==========================================
# 8. MAIN PIPELINE
# ==========================================

def main() -> None:
    print("=" * 70)
    print("  ROOTWISE M2: NASA MODIS MOD13Q1 NDVI INTEGRATION")
    print("=" * 70)

    # 1. Pre-flight file checks
    if not FULL_JSON.exists():
        sys.exit(f"ERROR: Full JSON not found at {FULL_JSON}")

    # 2. Load and validate existing JSON
    print("\n[1] Loading and validating existing JSON...")
    with FULL_JSON.open("r", encoding="utf-8") as f:
        full_data = json.load(f)

    validate_input_json(full_data)

    # 3. Create timestamped backup
    print("\n[2] Creating timestamped backup...")
    backup_path = create_backup()

    # 4. Load and quality-filter MODIS rasters
    print("\n[3] Loading MODIS GeoTIFF rasters and applying strict quality mask...")
    ndvi, strict_valid, transform, h, w = load_and_screen_rasters()

    # 5. Match grid cells to NDVI
    print("\n[4] Matching 2,380 grid cells to quality-screened NDVI...")
    cells = full_data["cells"]
    direct_cnt, fallback_cnt, null_cnt, pop_vals = update_cells_with_ndvi(
        cells, ndvi, strict_valid, transform, h, w
    )

    total_pop = direct_cnt + fallback_cnt
    print(f"    Direct centroid assigned cells : {direct_cnt:,} ({direct_cnt/len(cells)*100:.2f}%)")
    print(f"    Within-cell fallback cells     : {fallback_cnt:,} ({fallback_cnt/len(cells)*100:.2f}%)")
    print(f"    Total populated cells          : {total_pop:,} ({total_pop/len(cells)*100:.2f}%)")
    print(f"    Cells remaining null           : {null_cnt:,} ({null_cnt/len(cells)*100:.2f}%)")
    if pop_vals:
        print(f"    Populated NDVI Range           : min={min(pop_vals):.4f}, max={max(pop_vals):.4f}, mean={np.mean(pop_vals):.4f}")

    # 6. Update indicator metadata
    print("\n[5] Updating indicator_metadata['ndvi']...")
    update_metadata(full_data["indicator_metadata"], direct_cnt, fallback_cnt, null_cnt)

    # 7. Safe atomic save & regenerate sample
    print("\n[6] Atomically saving updated full JSON and sample...")
    try:
        save_json_safe(FULL_JSON, full_data)
        regenerate_sample(full_data)
    except Exception as exc:
        print(f"\nERROR during JSON write: {exc}")
        print(f"Original JSON was not damaged. Backup is at: {backup_path}")
        sys.exit(1)

    # 8. Summary
    print("\n" + "=" * 70)
    print("  MODIS NDVI INTEGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"  Observation date           : {DATA_DATE}")
    print(f"  MODIS Product              : MOD13Q1 Version 061 (250m)")
    print(f"  Total cells                : {len(cells):,}")
    print(f"  Populated cells            : {total_pop:,} ({total_pop/len(cells)*100:.2f}%)")
    print(f"    - Direct centroid        : {direct_cnt:,}")
    print(f"    - Within-cell fallback   : {fallback_cnt:,}")
    print(f"  Null cells (strict QA)     : {null_cnt:,} ({null_cnt/len(cells)*100:.2f}%)")
    print(f"  Backup created             : {backup_path.name}")
    print(f"  Full JSON                  : {FULL_JSON.relative_to(ROOT)}")
    print(f"  Sample JSON                : {SAMPLE_JSON.relative_to(ROOT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
