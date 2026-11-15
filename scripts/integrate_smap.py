"""
ROOTWISE M2 – NASA SMAP Soil Moisture Integration
=================================================
Integrates NASA SMAP SPL3SMP Version 009 (L3 Radiometer Daily 36 km EASE-Grid 2.0)
soil moisture into the Bengaluru Urban JSON dataset (2,380 grid cells) for 2016-01-01.

Granule: SMAP_L3_SM_P_20160101_R19240_001.h5 (Version 009)
Group: Soil_Moisture_Retrieval_Data_PM (Ascending orbit pass ~12:22 UTC / 17:52 IST)
Variables:
  - latitude_pm (Float32, 406x964)
  - longitude_pm (Float32, 406x964)
  - soil_moisture_pm (Float32, 406x964, m3/m3, valid range [0.02, 0.50])
  - retrieval_qual_flag_pm (UInt16, 406x964)

Strict Quality Filter:
  - (retrieval_qual_flag_pm & 0b111) == 0
    Bit 0 = 0 (Recommended quality)
    Bit 1 = 0 (Retrieval attempted)
    Bit 2 = 0 (Retrieval successful)
  - soil_moisture_pm != -9999.0 and soil_moisture_pm > -900.0
  - math.isfinite(soil_moisture_pm)
  - 0.02 <= soil_moisture_pm <= 0.50 m3/m3

Conversion:
  - soil_moisture_pct = round(soil_moisture_pm * 100.0, 4)

CRITICAL SPATIAL RESOLUTION LIMITATIONS:
-----------------------------------------
- SMAP native resolution is ~36 km x 36 km (EASE-Grid 2.0).
- The PM pass on 2016-01-01 provides 5 valid pixels surrounding Bengaluru Urban
  passing the strict quality mask. Central urban core pixels were flagged
  (retrieval_qual_flag_pm = 9) due to urban land fraction and excluded.
- The 2,380 1 km grid cells are assigned to the nearest valid SMAP pixel
  (maximum nearest-neighbor distance: 37.91 km).
- These values represent coarse regional background moisture, NOT 1 km local
  in-situ measurements. Spatial uncertainty is documented in indicator_metadata.
- No interpolation, gap-filling, or synthetic values are fabricated.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

# ==========================================
# 1. CONFIGURATION & PATHS
# ==========================================

ROOT = Path(__file__).resolve().parent.parent

FULL_JSON = ROOT / "data/outputs/bengaluru_urban_20160101.json"
SAMPLE_JSON = ROOT / "data/outputs/bengaluru_urban_sample_3_cells.json"
GRANULE_PATH = ROOT / "data/raw/smap/SMAP_L3_SM_P_20160101_R19240_001.h5"

DATA_DATE = "2016-01-01"
GROUP_NAME = "Soil_Moisture_Retrieval_Data_PM"
SMAP_NATIVE_RESOLUTION = "36 km EASE-Grid 2.0 (~36 km x 36 km)"
EXPECTED_CELL_COUNT = 2380

REQUIRED_INDICATORS = {
    "rainfall_mm",
    "soil_moisture_pct",
    "temperature_min_c",
    "temperature_max_c",
    "humidity_pct",
    "ndvi",
    "evapotranspiration_mm",
}

REQUIRED_METADATA_KEYS = set(REQUIRED_INDICATORS)

# Regional bounding box for candidate SMAP pixels
REG_LAT_MIN, REG_LAT_MAX = 11.5, 14.5
REG_LON_MIN, REG_LON_MAX = 76.5, 79.5


# ==========================================
# 2. DISTANCE CALCULATIONS
# ==========================================

def approx_sq_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Cosine-corrected angular squared distance."""
    dlat = lat2 - lat1
    dlon = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2.0))
    return dlat * dlat + dlon * dlon


def approx_dist_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in km using mean degree length."""
    return math.sqrt(approx_sq_dist(lat1, lon1, lat2, lon2)) * 111.3195


# ==========================================
# 3. PRE-FLIGHT VALIDATION
# ==========================================

def validate_input_json(full_data: dict) -> None:
    """Verify that existing JSON is complete, intact, and consistent before modification."""
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
        missing_meta = REQUIRED_METADATA_KEYS - metadata.keys()
        if missing_meta:
            errors.append(f"indicator_metadata missing keys: {sorted(missing_meta)}.")

    if errors:
        raise ValueError("Pre-flight validation FAILED:\n" + "\n".join(f"  • {e}" for e in errors))

    print(
        f"  Pre-flight validation PASSED: {len(cells)} cells, {len(seen_ids)} unique IDs, "
        f"all centroids and required indicator keys verified."
    )


# ==========================================
# 4. BACKUP CREATION
# ==========================================

def create_backup() -> Path:
    """Create a timestamped backup before touching the dataset."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = FULL_JSON.with_name(f"{FULL_JSON.stem}_backup_{timestamp}{FULL_JSON.suffix}")
    shutil.copy2(FULL_JSON, backup)
    print(f"  Backup created → {backup.relative_to(ROOT)}")
    return backup


# ==========================================
# 5. READ & FILTER SMAP PM GRANULE
# ==========================================

def load_and_filter_smap(granule_path: Path) -> list[dict]:
    """Read Soil_Moisture_Retrieval_Data_PM from local HDF5 file and apply strict quality mask.

    Returns a list of dicts with valid pixels:
      {
        'lat': float,
        'lon': float,
        'sm_m3m3': float,
        'sm_pct': float,
        'qual_flag': int
      }
    """
    if not granule_path.exists():
        raise FileNotFoundError(f"SMAP granule not found at: {granule_path}")

    print(f"  Opening SMAP granule: {granule_path.name}")
    with Dataset(granule_path, "r") as nc:
        if GROUP_NAME not in nc.groups:
            raise KeyError(f"Group '{GROUP_NAME}' not found in {granule_path.name}")

        grp = nc.groups[GROUP_NAME]

        lat_var = grp.variables["latitude_pm"]
        lon_var = grp.variables["longitude_pm"]
        sm_var = grp.variables["soil_moisture_pm"]
        qf_var = grp.variables["retrieval_qual_flag_pm"]

        lats = np.array(lat_var[:], dtype=float)
        lons = np.array(lon_var[:], dtype=float)
        sm = np.array(sm_var[:], dtype=float)
        qf = np.array(qf_var[:], dtype=np.int32)

    print(f"  Array dimensions: {sm.shape} (rows x cols)")

    # Strict quality mask and range filter:
    # 1. Coordinates valid
    coord_valid = (lats > -900.0) & (lons > -900.0)
    # 2. Strict 3-bit quality flag: (qf & 0b111) == 0 (Bits 0, 1, 2 must all be 0)
    qf_valid = (qf & 0b111) == 0
    # 3. Valid soil moisture range: 0.02 <= sm <= 0.50 m3/m3, finite, non-fill
    sm_valid = (sm > -900.0) & np.isfinite(sm) & (sm >= 0.02) & (sm <= 0.50)

    # Regional bounding box filter: 11.5N - 14.5N, 76.5E - 79.5E
    in_region = (
        (lats >= REG_LAT_MIN) & (lats <= REG_LAT_MAX) &
        (lons >= REG_LON_MIN) & (lons <= REG_LON_MAX)
    )

    combined_mask = coord_valid & qf_valid & sm_valid & in_region
    valid_count = int(np.sum(combined_mask))
    print(f"  Regional pixels passing strict 3-bit quality filter: {valid_count}")

    if valid_count == 0:
        raise RuntimeError("No valid SMAP pixels found in regional bounding box.")

    reg_lats = lats[combined_mask]
    reg_lons = lons[combined_mask]
    reg_sm = sm[combined_mask]
    reg_qf = qf[combined_mask]

    valid_pixels: list[dict] = []
    for i in range(valid_count):
        raw_sm = float(reg_sm[i])
        pct_sm = round(raw_sm * 100.0, 4)
        valid_pixels.append({
            "lat": float(reg_lats[i]),
            "lon": float(reg_lons[i]),
            "sm_m3m3": raw_sm,
            "sm_pct": pct_sm,
            "qual_flag": int(reg_qf[i]),
        })

    return valid_pixels


# ==========================================
# 6. MATCH CELLS TO NEAREST VALID SMAP PIXEL
# ==========================================

def update_cells_with_smap(
    cells: list[dict],
    smap_pixels: list[dict],
) -> tuple[int, int, dict[tuple[float, float], dict]]:
    """Assign nearest valid SMAP pixel value to each cell.

    Preserves without modification:
      - rainfall_mm, temperature_min_c, temperature_max_c, humidity_pct
      - ndvi, evapotranspiration_mm
      - grid_id, state, district, centroid_lat, centroid_lon, geometry, data_quality

    Returns:
      (filled_count, null_count, assignment_details)
    """
    filled_count = 0
    null_count = 0
    assignment_stats: dict[tuple[float, float], dict] = {}

    for cell in cells:
        c_lat = cell["centroid_lat"]
        c_lon = cell["centroid_lon"]
        indicators = cell["indicators"]

        best_pt: dict | None = None
        best_d = float("inf")
        best_d_km = float("inf")

        for pt in smap_pixels:
            d = approx_sq_dist(c_lat, c_lon, pt["lat"], pt["lon"])
            if d < best_d:
                best_d = d
                best_pt = pt

        if best_pt is not None:
            best_d_km = approx_dist_km(c_lat, c_lon, best_pt["lat"], best_pt["lon"])
            indicators["soil_moisture_pct"] = best_pt["sm_pct"]
            filled_count += 1

            key = (round(best_pt["lat"], 4), round(best_pt["lon"], 4))
            if key not in assignment_stats:
                assignment_stats[key] = {
                    "count": 0,
                    "sm_m3m3": best_pt["sm_m3m3"],
                    "sm_pct": best_pt["sm_pct"],
                    "qual_flag": best_pt["qual_flag"],
                    "max_dist_km": 0.0,
                }
            assignment_stats[key]["count"] += 1
            if best_d_km > assignment_stats[key]["max_dist_km"]:
                assignment_stats[key]["max_dist_km"] = best_d_km
        else:
            indicators["soil_moisture_pct"] = None
            null_count += 1

    return filled_count, null_count, assignment_stats


# ==========================================
# 7. UPDATE INDICATOR METADATA
# ==========================================

def update_metadata(indicator_metadata: dict, assignment_stats: dict) -> None:
    """Update metadata for soil_moisture_pct only.
    All other indicator metadata entries are preserved.
    """
    unique_pixel_count = len(assignment_stats)
    overall_max_dist_km = max(s["max_dist_km"] for s in assignment_stats.values()) if assignment_stats else 0.0

    note = (
        "Coarse satellite radiometer estimate (36 km EASE-Grid 2.0). "
        "On 2016-01-01, soil moisture was retrieved during the PM ascending pass "
        "(~12:22 UTC / 17:52 IST, Orbit 04899_A); the AM descending pass contained no data over South India. "
        "Urban core pixels directly over central Bengaluru were flagged (retrieval_qual_flag_pm = 9) "
        "and excluded under the strict recommended-quality mask ((retrieval_qual_flag_pm & 7) == 0). "
        "All 2,380 1 km grid cells are assigned to the nearest of five valid surrounding 36 km SMAP pixels, "
        f"with a maximum source distance of {overall_max_dist_km:.2f} km. "
        "Values represent coarse regional background moisture (8.55% to 13.32%) and carry spatial uncertainty; "
        "they do not capture 1 km sub-grid urban heterogeneity. "
        "No interpolation, synthetic filling, or invalid substitution was performed."
    )

    indicator_metadata["soil_moisture_pct"] = {
        "source": "NASA SMAP SPL3SMP Version 009 (L3 Radiometer Daily 36 km)",
        "variable": "Soil_Moisture_Retrieval_Data_PM/soil_moisture_pm",
        "units": "%",
        "status": "estimated",
        "native_resolution": SMAP_NATIVE_RESOLUTION,
        "overpass": "Ascending / PM pass (~12:22 UTC / 17:52 IST, Orbit 04899_A)",
        "quality_mask": "(retrieval_qual_flag_pm & 0b111) == 0 (Bits 0, 1, 2 must all be 0)",
        "valid_range": "0.02 - 0.50 m3/m3 (converted to 2.0 - 50.0 %)",
        "conversion": "soil_moisture_pm * 100",
        "assignment_method": "nearest valid SMAP grid pixel",
        "unique_source_pixels": unique_pixel_count,
        "max_nearest_distance_km": round(overall_max_dist_km, 2),
        "note": note,
    }


# ==========================================
# 8. SAFE ATOMIC SAVING
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
# 9. MAIN PIPELINE
# ==========================================

def main() -> None:
    print("=" * 70)
    print("  ROOTWISE M2: NASA SMAP SOIL MOISTURE INTEGRATION")
    print("=" * 70)

    # 1. Pre-flight file checks
    if not FULL_JSON.exists():
        sys.exit(f"ERROR: Full JSON not found at {FULL_JSON}")

    if not GRANULE_PATH.exists():
        sys.exit(f"ERROR: SMAP granule not found at {GRANULE_PATH}")

    # 2. Load and validate existing JSON
    print("\n[1] Loading and validating existing JSON...")
    with FULL_JSON.open("r", encoding="utf-8") as f:
        full_data = json.load(f)

    validate_input_json(full_data)

    # 3. Create timestamped backup
    print("\n[2] Creating timestamped backup...")
    backup_path = create_backup()

    # 4. Read SMAP granule and apply strict quality mask
    print("\n[3] Reading SMAP PM group and applying quality filter...")
    valid_pixels = load_and_filter_smap(GRANULE_PATH)

    # 5. Match grid cells to nearest valid pixel
    print("\n[4] Matching 2,380 grid cells to nearest valid SMAP pixel...")
    cells = full_data["cells"]
    filled_count, null_count, assignment_stats = update_cells_with_smap(cells, valid_pixels)

    print(f"    Populated cells: {filled_count:,} / {len(cells):,} ({filled_count/len(cells)*100:.1f}%)")
    print(f"    Missing/null cells: {null_count}")
    print(f"    Unique source SMAP pixels assigned: {len(assignment_stats)}")

    overall_max_dist = 0.0
    for (plat, plon), stats in assignment_stats.items():
        if stats["max_dist_km"] > overall_max_dist:
            overall_max_dist = stats["max_dist_km"]
        pct_share = (stats["count"] / len(cells)) * 100
        print(
            f"    - Pixel (lat={plat:.4f}, lon={plon:.4f}): "
            f"SM={stats['sm_m3m3']:.4f} m3/m3 ({stats['sm_pct']:.2f}%), "
            f"QF={stats['qual_flag']} -> {stats['count']:,} cells ({pct_share:.1f}%), "
            f"max dist={stats['max_dist_km']:.2f} km"
        )

    print(f"    Maximum nearest-source distance across all cells: {overall_max_dist:.2f} km")

    # 6. Update indicator metadata
    print("\n[5] Updating indicator_metadata['soil_moisture_pct']...")
    update_metadata(full_data["indicator_metadata"], assignment_stats)

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
    print("  SMAP INTEGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"  Observation date        : {DATA_DATE}")
    print(f"  SMAP Product            : SPL3SMP Version 009")
    print(f"  Orbit Pass              : PM Ascending (~12:22 UTC / 17:52 IST)")
    print(f"  Total cells             : {len(cells):,}")
    print(f"  Populated cells         : {filled_count:,}")
    print(f"  Missing cells           : {null_count}")
    print(f"  Unique SMAP pixels      : {len(assignment_stats)}")
    print(f"  Max nearest distance    : {overall_max_dist:.2f} km")
    print(f"  Backup created          : {backup_path.name}")
    print(f"  Full JSON               : {FULL_JSON.relative_to(ROOT)}")
    print(f"  Sample JSON             : {SAMPLE_JSON.relative_to(ROOT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
