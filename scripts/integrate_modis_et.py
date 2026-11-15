"""
ROOTWISE M2 – NASA MODIS MOD16A2GF Evapotranspiration Integration
==================================================================
Integrates NASA MODIS/Terra MOD16A2GF Version 061 (8-Day L4 Global 500m
Year-End Gap-Filled) Evapotranspiration into the Bengaluru Urban dataset
(2,380 grid cells) for 2016-01-01.

Product Details:
  - Product Name      : MOD16A2GF Version 061 (LP DAAC)
  - Composite Window  : 2016-01-01 to 2016-01-08 (8 calendar days, DOY 2016001)
  - Target Indicator  : evapotranspiration_mm
  - Native Resolution : 500 m Sinusoidal Grid (~463.31 m x 463.31 m)
  - Native Units      : kg/m^2/8day == mm/8day (accumulated over 8 days)
  - Scale Factor      : 0.1 (physical_et = raw * 0.1)
  - Valid Raw Range   : -32767 to 32700 (-3276.7 to +3270.0 mm/8day)
  - Special Codes     : 32761 (unclassified), 32762 (urban), 32763 (wetland),
                        32764 (snow), 32765 (barren), 32766 (water), 32767 (fill)
                        -> All special codes strictly preserved as null.

Quality Control Policy:
  Per NASA MOD16 C6.1 User Guide, gap-filling applies exclusively to LAI/FPAR
  inputs; users do not reject Bit 0 == 1. Primary check is valid raw range
  excluding special codes 32761-32767. QC flags are preserved for diagnostics.

Spatial Assignment Strategy:
  1. Centroid point sampling: If cell centroid falls on a valid physical ET
     pixel, assign: evapotranspiration_mm = round(raw * 0.1, 4).
  2. Within-cell polygon fallback: If centroid is urban/special/fill, query
     all valid 500 m pixel centers strictly inside that 1 km cell polygon.
     If >= 1 valid pixels exist inside the cell, assign their arithmetic mean:
     evapotranspiration_mm = round(mean(valid_inside_raw) * 0.1, 4).
  3. Null preservation: If zero valid physical ET pixels exist inside the cell
     polygon (e.g. pure urban core or water), assign null. Never borrow pixels
     outside the cell polygon, and never interpolate.

Safety:
  - Pre-flight validation of existing JSON and rasters.
  - Timestamped backup created before any file modification.
  - Safe atomic write via temporary file replacement.
  - Refresh sample JSON (first 3 cells).
  - All six existing indicators, grid IDs, CRS, and geometries are preserved 100%.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.transform import rowcol, xy
from shapely.geometry import Point, shape

# ==========================================
# 1. CONFIGURATION & FILE PATHS
# ==========================================

ROOT = Path(__file__).resolve().parent.parent

FULL_JSON = ROOT / "data/outputs/bengaluru_urban_20160101.json"
SAMPLE_JSON = ROOT / "data/outputs/bengaluru_urban_sample_3_cells.json"
MODIS_DIR = ROOT / "data/raw/modis"

ET_FILE = MODIS_DIR / "MOD16A2GF.061_ET_500m_doy2016001000000_aid0001.tif"
QC_FILE = MODIS_DIR / "MOD16A2GF.061_ET_QC_500m_doy2016001000000_aid0001.tif"

DATA_DATE = "2016-01-01"
EXPECTED_CELL_COUNT = 2380
SCALE_FACTOR = 0.1

SPECIAL_CODES = {
    32761: "Unclassified land cover",
    32762: "Urban / Built-up land cover",
    32763: "Permanent wetland",
    32764: "Permanent snow / ice",
    32765: "Barren / sparsely vegetated",
    32766: "Water body",
    32767: "Nodata fill value",
}

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

def validate_input_json(full_data: dict[str, Any]) -> None:
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

def load_and_screen_rasters() -> tuple[np.ndarray, np.ndarray, np.ndarray, rasterio.Affine, int, int]:
    """Load the ET and QC GeoTIFFs, verify alignment, and generate the valid physical ET mask.

    Returns:
      (et_array, qc_array, valid_physical_mask, transform, height, width)
    """
    for p in [ET_FILE, QC_FILE]:
        if not p.exists():
            raise FileNotFoundError(f"Required MODIS GeoTIFF not found: {p}")

    with rasterio.open(ET_FILE) as s_et, rasterio.open(QC_FILE) as s_qc:
        # Spatial alignment checks
        if s_et.shape != s_qc.shape:
            raise ValueError(f"Raster shape mismatch: ET={s_et.shape}, QC={s_qc.shape}")
        if s_et.transform != s_qc.transform:
            raise ValueError("Raster affine transform mismatch between ET and QC.")
        if s_et.crs != s_qc.crs or s_et.crs.to_string() != "EPSG:4326":
            raise ValueError(f"Expected CRS EPSG:4326, got ET={s_et.crs}, QC={s_qc.crs}")
        if s_et.bounds != s_qc.bounds:
            raise ValueError("Raster spatial bounds mismatch between ET and QC.")

        et = s_et.read(1)
        qc = s_qc.read(1)
        transform = s_et.transform
        h, w = et.shape
        nodata = s_et.nodata

    # Valid physical ET condition:
    # 1. -32767 <= raw <= 32700
    # 2. raw not in special land-cover codes (32761..32767)
    # 3. raw != nodata
    # 4. math.isfinite(raw)
    valid_physical_mask = (
        (et >= -32767)
        & (et <= 32700)
        & (~np.isin(et, list(SPECIAL_CODES.keys())))
        & (et != nodata)
        & np.isfinite(et)
    )

    total_valid = int(np.sum(valid_physical_mask))
    print(f"  Raster dimensions: {w} x {h} ({et.size:,} pixels)")
    print(f"  Pixels passing physical validity screen: {total_valid:,} / {et.size:,} ({total_valid/et.size*100:.2f}%)")

    return et, qc, valid_physical_mask, transform, h, w


# ==========================================
# 5. MATCH ET TO GRID CELLS
# ==========================================

def update_cells_with_et(
    cells: list[dict[str, Any]],
    et: np.ndarray,
    qc: np.ndarray,
    valid_mask: np.ndarray,
    transform: rasterio.Affine,
    h: int,
    w: int,
) -> tuple[int, int, int, list[float], dict[str, Any]]:
    """Assign quality-screened ET to each 1 km cell.

    Assignment rules:
      1. Centroid point sampling: if valid physical pixel at centroid, use it.
      2. Within-cell polygon fallback: if centroid invalid, calculate arithmetic
         mean of all valid physical pixels whose center coordinates lie inside
         that 1 km cell polygon.
      3. If no valid physical pixel lies inside the cell, assign None (null).
         Never use pixels outside the cell polygon.

    Returns:
      (direct_count, fallback_count, null_count, populated_values, qc_diagnostics)
    """
    # Precompute pixel center coordinates in WGS84
    cols_grid, rows_grid = np.meshgrid(np.arange(w), np.arange(h))
    xs_flat, ys_flat = xy(transform, rows_grid.flatten(), cols_grid.flatten(), offset="center")
    xs = np.array(xs_flat).reshape((h, w))
    ys = np.array(ys_flat).reshape((h, w))

    direct_count = 0
    fallback_count = 0
    null_count = 0
    populated_values: list[float] = []

    # QC diagnostic trackers
    centroid_qc_vals: list[int] = []

    for cell in cells:
        c_lat = cell["centroid_lat"]
        c_lon = cell["centroid_lon"]
        indicators = cell["indicators"]
        geom = shape(cell["geometry"])

        # Row and column for centroid
        r_c = int((c_lat - transform.f) / transform.e)
        c_c = int((c_lon - transform.c) / transform.a)

        # 1. Centroid point sampling
        if (0 <= r_c < h) and (0 <= c_c < w):
            centroid_qc_vals.append(int(qc[r_c, c_c]))
            if valid_mask[r_c, c_c]:
                raw_val = float(et[r_c, c_c])
                val_scaled = round(raw_val * SCALE_FACTOR, 4)
                indicators["evapotranspiration_mm"] = val_scaled
                direct_count += 1
                populated_values.append(val_scaled)
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
        sub_valid = valid_mask[sub_r, sub_c]

        valid_inside_raw: list[float] = []
        for ri, ci in zip(sub_r[sub_valid], sub_c[sub_valid]):
            px_pt = Point(xs[ri, ci], ys[ri, ci])
            if geom.contains(px_pt):
                valid_inside_raw.append(float(et[ri, ci]))

        if len(valid_inside_raw) > 0:
            mean_scaled = round(float(np.mean(valid_inside_raw)) * SCALE_FACTOR, 4)
            indicators["evapotranspiration_mm"] = mean_scaled
            fallback_count += 1
            populated_values.append(mean_scaled)
        else:
            # 3. Retain null (never use pixels outside the cell polygon)
            indicators["evapotranspiration_mm"] = None
            null_count += 1

    # QC diagnostic summary
    qc_arr = np.array(centroid_qc_vals)
    valid_qc = qc_arr[qc_arr != 255]
    bit0 = valid_qc & 1
    cloud = (valid_qc >> 3) & 3

    qc_diagnostics = {
        "evaluated_centroid_pixels": len(centroid_qc_vals),
        "valid_qc_pixels": len(valid_qc),
        "primary_lai_input_cells_bit0_zero": int(np.sum(bit0 == 0)),
        "gapfilled_lai_input_cells_bit0_one": int(np.sum(bit0 == 1)),
        "cloud_state_clear_cells": int(np.sum(cloud == 0)),
        "cloud_state_mixed_cells": int(np.sum(cloud == 2)),
        "cloud_state_assumed_clear_cells": int(np.sum(cloud == 3)),
        "cloud_state_cloud_cells": int(np.sum(cloud == 1)),
    }

    return direct_count, fallback_count, null_count, populated_values, qc_diagnostics


# ==========================================
# 6. UPDATE INDICATOR METADATA
# ==========================================

def update_metadata(
    indicator_metadata: dict[str, Any],
    direct_count: int,
    fallback_count: int,
    null_count: int,
    qc_diagnostics: dict[str, Any],
) -> None:
    """Update metadata for evapotranspiration_mm only. All other indicator entries are preserved."""
    total_pop = direct_count + fallback_count
    coverage_pct = round((total_pop / EXPECTED_CELL_COUNT) * 100, 2)

    note = (
        "8-day accumulated evapotranspiration from NASA MODIS/Terra MOD16A2GF Collection 6.1 "
        "(500m Sinusoidal Grid, tile h25v07, year-end gap-filled science product). "
        "Values represent total evapotranspiration in mm accumulated over the 8-day composite period "
        "from 2016-01-01 through 2016-01-08 (DOY 001-008); they are NOT single-day rates. "
        "To obtain the equivalent mean daily evapotranspiration rate, divide by 8 (daily_rate_divisor: 8). "
        "Each 1 km cell was matched against valid 500 m physical retrievals (raw range -32767 to 32700, "
        f"scale factor 0.1). Centroid sampling was used where valid physical pixels covered the cell center ({direct_count:,} cells); "
        f"within-cell arithmetic mean of valid interior pixels was used as fallback ({fallback_count:,} cells). "
        f"Cells where all interior pixels represent unmodeled surfaces remain strictly null ({null_count:,} cells, "
        "primarily urban/built-up land cover [code 32762] and water bodies [code 32766] where Penman-Monteith "
        "does not retrieve transpiration). No spatial interpolation or outside-cell borrowing was performed. "
        "Per NASA MOD16 Collection 6.1 guidance, the gap-filled product MOD16A2GF screens input LAI/FPAR climatologically; "
        f"QC diagnostics at cell centroids record {qc_diagnostics['primary_lai_input_cells_bit0_zero']:,} primary LAI retrievals "
        f"and {qc_diagnostics['gapfilled_lai_input_cells_bit0_one']:,} gap-filled LAI retrievals."
    )

    indicator_metadata["evapotranspiration_mm"] = {
        "source": "NASA MODIS Terra MOD16A2GF Version 061 (8-Day L4 Global 500m)",
        "variable": "ET_500m",
        "units": "mm/8day (accumulated over 8-day composite 2016-01-01 to 2016-01-08)",
        "scale_factor": SCALE_FACTOR,
        "status": "observed",
        "native_resolution": "500 m Sinusoidal Grid (~463.31 m x 463.31 m)",
        "temporal_coverage": "2016-01-01 to 2016-01-08 (8-day composite, DOY 001-008)",
        "temporal_accumulation": "8-day total (not daily ET rate; daily divisor is 8)",
        "daily_rate_divisor": 8,
        "tile": "h25v07",
        "valid_raw_range": "-32767 to 32700",
        "physical_valid_range": "-3276.7 to 3270.0 mm/8day",
        "special_fill_codes": "32761 (unclassified), 32762 (urban), 32763 (wetland), 32764 (snow), 32765 (barren), 32766 (water), 32767 (fill)",
        "quality_policy": "Documented valid raw range excluding special codes 32761-32767. ET_QC_500m Bit 0 recorded for diagnostics per NASA MOD16 GF user guide.",
        "assignment_method": "Centroid 500m pixel sampling, with within-cell 500m pixel mean fallback; null otherwise",
        "direct_centroid_cells": direct_count,
        "fallback_within_cell_cells": fallback_count,
        "null_cells": null_count,
        "total_populated_cells": total_pop,
        "coverage_pct": coverage_pct,
        "qc_diagnostics": qc_diagnostics,
        "note": note,
    }


# ==========================================
# 7. SAFE ATOMIC SAVING
# ==========================================

def save_json_safe(path: Path, content: dict[str, Any]) -> None:
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


def regenerate_sample(full_data: dict[str, Any]) -> None:
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
    print("  ROOTWISE M2: NASA MODIS MOD16A2GF EVAPOTRANSPIRATION INTEGRATION")
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

    # 4. Load and quality-filter MODIS ET rasters
    print("\n[3] Loading MODIS GeoTIFF rasters and applying physical validity screen...")
    et, qc, valid_mask, transform, h, w = load_and_screen_rasters()

    # 5. Match grid cells to ET
    print("\n[4] Matching 2,380 grid cells to quality-screened ET...")
    cells = full_data["cells"]
    direct_cnt, fallback_cnt, null_cnt, pop_vals, qc_diag = update_cells_with_et(
        cells, et, qc, valid_mask, transform, h, w
    )

    total_pop = direct_cnt + fallback_cnt
    print(f"    Direct centroid assigned cells : {direct_cnt:,} ({direct_cnt/len(cells)*100:.2f}%)")
    print(f"    Within-cell fallback cells     : {fallback_cnt:,} ({fallback_cnt/len(cells)*100:.2f}%)")
    print(f"    Total populated cells          : {total_pop:,} ({total_pop/len(cells)*100:.2f}%)")
    print(f"    Cells remaining null           : {null_cnt:,} ({null_cnt/len(cells)*100:.2f}%)")
    if pop_vals:
        print(f"    Populated 8-day ET Range       : min={min(pop_vals):.4f}, max={max(pop_vals):.4f}, mean={np.mean(pop_vals):.4f} mm/8day")
        print(f"    Daily Equivalent Rate Range    : min={min(pop_vals)/8:.4f}, max={max(pop_vals)/8:.4f}, mean={np.mean(pop_vals)/8:.4f} mm/day")

    # 6. Update indicator metadata
    print("\n[5] Updating indicator_metadata['evapotranspiration_mm']...")
    update_metadata(full_data["indicator_metadata"], direct_cnt, fallback_cnt, null_cnt, qc_diag)

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
    print("  MODIS ET INTEGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"  Observation date           : {DATA_DATE}")
    print(f"  MODIS Product              : MOD16A2GF Version 061 (500m)")
    print(f"  Total cells                : {len(cells):,}")
    print(f"  Populated cells            : {total_pop:,} ({total_pop/len(cells)*100:.2f}%)")
    print(f"    - Direct centroid        : {direct_cnt:,}")
    print(f"    - Within-cell fallback   : {fallback_cnt:,}")
    print(f"  Null cells (unmodeled/fill): {null_cnt:,} ({null_cnt/len(cells)*100:.2f}%)")
    print(f"  Backup created             : {backup_path.name}")
    print(f"  Full JSON                  : {FULL_JSON.relative_to(ROOT)}")
    print(f"  Sample JSON                : {SAMPLE_JSON.relative_to(ROOT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
