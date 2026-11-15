"""
ROOTWISE M2 – NASA MODIS MOD16A2GF Evapotranspiration Raster Inspection
========================================================================
Performs a strict read-only inspection of the downloaded NASA AppEEARS
MODIS MOD16A2GF.061 GeoTIFF rasters for Bengaluru Urban (2016-01-01 to 2016-01-08).

Target Layers:
1. ET_500m    : 8-day accumulated ET (kg/m^2/8day == mm/8day)
2. ET_QC_500m : Evapotranspiration Quality Control flags (uint8 bit field)

Requirements:
- Read-only: does not modify, rescale, or delete any file.
- Checks CRS, dimensions, transform, nodata, bounds, and data types.
- Analyzes raw values, special non-vegetated codes (32761-32767), and negative values.
- Analyzes ET_QC bit distribution (Bit 0 primary vs gap-filled, Bits 3-4 cloud state).
- Evaluates spatial coverage across all 2,380 Bengaluru Urban grid cells.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.transform import xy
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parent.parent
RAW_MODIS = ROOT / "data/raw/modis"
OUTPUT_JSON = ROOT / "data/outputs/bengaluru_urban_20160101.json"

SPECIAL_CODES = {
    32761: "Unclassified land cover",
    32762: "Urban / Built-up land cover",
    32763: "Permanent wetland",
    32764: "Permanent snow / ice",
    32765: "Barren / sparsely vegetated",
    32766: "Water body",
    32767: "Nodata fill value",
}


def find_geotiff(pattern: str) -> Path | None:
    matches = list(RAW_MODIS.glob(pattern))
    if not matches:
        return None
    # Prefer exact doy2016001 match
    for m in matches:
        if "2016001" in m.name:
            return m
    return matches[0]


def inspect_raster(path: Path, layer_type: str) -> dict[str, Any]:
    print(f"\n--- Layer: {layer_type} ({path.name}) ---")
    size_kb = path.stat().st_size / 1024
    print(f"  File size         : {size_kb:.2f} KB ({path.stat().st_size:,} bytes)")

    with rasterio.open(path) as src:
        crs = src.crs
        width, height = src.width, src.height
        count = src.count
        dtype = src.dtypes[0]
        nodata = src.nodata
        bounds = src.bounds
        res = src.res
        data = src.read(1)

    print(f"  CRS               : {crs}")
    print(f"  Dimensions        : {width} x {height} ({width * height:,} total pixels)")
    print(f"  Band count        : {count}")
    print(f"  Data type         : {dtype}")
    print(f"  Nodata value      : {nodata}")
    print(f"  Pixel resolution  : {res[0]:.8f}° x {res[1]:.8f}° (~{res[0]*111195:.1f} m)")
    print(f"  Bounds (WGS84)    : Left={bounds.left:.6f}, Bottom={bounds.bottom:.6f}, "
          f"Right={bounds.right:.6f}, Top={bounds.top:.6f}")

    return {
        "path": path,
        "crs": crs,
        "width": width,
        "height": height,
        "count": count,
        "dtype": dtype,
        "nodata": nodata,
        "bounds": bounds,
        "res": res,
        "data": data,
    }


def analyze_et(et_dict: dict[str, Any]) -> None:
    data = et_dict["data"]
    nodata = et_dict["nodata"]
    total_pixels = data.size

    print("\n[ET_500m Raw Value Analysis]")
    print(f"  Total raster pixels       : {total_pixels:,}")

    # Special fill codes breakdown
    print("  Special Land Cover / Fill Codes Distribution:")
    special_counts = {}
    for code, desc in SPECIAL_CODES.items():
        cnt = int(np.sum(data == code))
        special_counts[code] = cnt
        pct = (cnt / total_pixels) * 100
        print(f"    Code {code} ({desc:<28}): {cnt:>6,} pixels ({pct:>5.2f}%)")

    total_special = sum(special_counts.values())

    # Valid raw data mask
    # -32767 <= raw <= 32700, and not in special codes, and not nodata
    valid_mask = (
        (data >= -32767)
        & (data <= 32700)
        & (~np.isin(data, list(SPECIAL_CODES.keys())))
        & (data != nodata)
    )
    valid_raw = data[valid_mask]
    valid_count = len(valid_raw)
    valid_pct = (valid_count / total_pixels) * 100

    print(f"\n  Valid Physical ET Pixels  : {valid_count:,} ({valid_pct:.2f}%)")

    if valid_count > 0:
        min_raw = int(np.min(valid_raw))
        max_raw = int(np.max(valid_raw))
        mean_raw = float(np.mean(valid_raw))

        min_scaled = min_raw * 0.1
        max_scaled = max_raw * 0.1
        mean_scaled = mean_raw * 0.1

        print(f"  Raw value range           : [{min_raw}, {max_raw}], mean = {mean_raw:.2f}")
        print(f"  Physical ET (8-day accum) : [{min_scaled:.2f}, {max_scaled:.2f}] mm/8day, "
              f"mean = {mean_scaled:.2f} mm/8day")
        print(f"  Daily equivalent rate     : [{min_scaled/8:.3f}, {max_scaled/8:.3f}] mm/day, "
              f"mean = {mean_scaled/8:.3f} mm/day")

        # Check negative ET
        neg_count = int(np.sum(valid_raw < 0))
        if neg_count > 0:
            print(f"  Valid Negative ET Pixels  : {neg_count:,} (condensation / dew flux observed)")
        else:
            print("  Valid Negative ET Pixels  : 0 (all valid retrievals are >= 0)")


def analyze_qc(qc_dict: dict[str, Any]) -> None:
    data = qc_dict["data"]
    nodata = qc_dict["nodata"]
    total_pixels = data.size

    print("\n[ET_QC_500m Quality Flag Analysis]")
    valid_qc = data[data != nodata]
    print(f"  Total pixels with valid QC: {len(valid_qc):,} / {total_pixels:,}")

    if len(valid_qc) == 0:
        return

    # Bit 0: MODLAND QC
    bit0 = valid_qc & 0b1
    bit0_counts = Counter(bit0)
    print("  Bit 0 (MODLAND QC - LAI Source):")
    print(f"    0 = Primary / Unfilled LAI input used : {bit0_counts.get(0, 0):,} pixels "
          f"({bit0_counts.get(0, 0)/len(valid_qc)*100:.2f}%)")
    print(f"    1 = Climatology / Gap-filled LAI used : {bit0_counts.get(1, 0):,} pixels "
          f"({bit0_counts.get(1, 0)/len(valid_qc)*100:.2f}%)")

    # Bits 3-4: Cloud State
    cloud_state = (valid_qc >> 3) & 0b11
    cloud_labels = {
        0b00: "00 = Clear",
        0b01: "01 = Cloud",
        0b10: "10 = Mixed Cloud",
        0b11: "11 = Assumed Clear",
    }
    cloud_counts = Counter(cloud_state)
    print("  Bits 3-4 (Cloud State):")
    for val, label in cloud_labels.items():
        cnt = cloud_counts.get(val, 0)
        pct = (cnt / len(valid_qc)) * 100
        print(f"    {label:<20}: {cnt:>6,} pixels ({pct:>5.2f}%)")

    # Bits 5-7: SCF Method
    scf_method = (valid_qc >> 5) & 0b111
    scf_labels = {
        0b000: "000 = Main RT method",
        0b001: "001 = Main RT with saturation",
        0b010: "010 = Empirical fallback 1",
        0b011: "011 = Empirical fallback 2",
        0b100: "100 = Not produced",
    }
    scf_counts = Counter(scf_method)
    print("  Bits 5-7 (SCF Method Score):")
    for val, label in scf_labels.items():
        cnt = scf_counts.get(val, 0)
        if cnt > 0:
            pct = (cnt / len(valid_qc)) * 100
            print(f"    {label:<30}: {cnt:>6,} pixels ({pct:>5.2f}%)")


def evaluate_grid_coverage(et_dict: dict[str, Any], qc_dict: dict[str, Any]) -> None:
    if not OUTPUT_JSON.exists():
        print(f"\nTarget JSON not found at {OUTPUT_JSON}. Skipping grid cell overlay.")
        return

    print("\n[Grid Overlay Pre-Screening: 2,380 Bengaluru Urban Cells]")
    with OUTPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cells = data.get("cells", [])
    print(f"  Loaded cells from JSON: {len(cells):,}")

    et_data = et_dict["data"]
    et_nodata = et_dict["nodata"]
    et_path = et_dict["path"]

    with rasterio.open(et_path) as src:
        transform = src.transform
        bounds = src.bounds
        h, w = src.shape

        # Precompute pixel centers in 2D (h, w)
        cols_grid, rows_grid = np.meshgrid(np.arange(w), np.arange(h))
        xs_flat, ys_flat = xy(transform, rows_grid.flatten(), cols_grid.flatten(), offset="center")
        xs = np.array(xs_flat).reshape((h, w))
        ys = np.array(ys_flat).reshape((h, w))

    valid_mask = (
        (et_data >= -32767)
        & (et_data <= 32700)
        & (~np.isin(et_data, list(SPECIAL_CODES.keys())))
        & (et_data != et_nodata)
    )

    direct_centroid_cells = 0
    urban_centroid_cells = 0
    nodata_centroid_cells = 0
    other_special_centroid_cells = 0
    fallback_eligible_cells = 0
    unresolvable_cells = 0

    centroid_et_values: list[float] = []

    for cell in cells:
        lat = cell["centroid_lat"]
        lon = cell["centroid_lon"]

        # Find row, col for centroid
        col = int((lon - transform.c) / transform.a)
        row = int((lat - transform.f) / transform.e)

        is_inside_raster = (0 <= row < h) and (0 <= col < w)

        if not is_inside_raster:
            nodata_centroid_cells += 1
            has_centroid_valid = False
        else:
            raw_val = int(et_data[row, col])
            if valid_mask[row, col]:
                direct_centroid_cells += 1
                centroid_et_values.append(raw_val * 0.1)
                has_centroid_valid = True
            elif raw_val == 32762:
                urban_centroid_cells += 1
                has_centroid_valid = False
            elif raw_val in SPECIAL_CODES:
                other_special_centroid_cells += 1
                has_centroid_valid = False
            else:
                nodata_centroid_cells += 1
                has_centroid_valid = False

        # If centroid invalid, check within-cell polygon fallback
        if not has_centroid_valid:
            poly = shape(cell["geometry"])
            poly_minx, poly_miny, poly_maxx, poly_maxy = poly.bounds

            r0 = max(0, int((poly_maxy - transform.f) / transform.e))
            r1 = min(h - 1, int((poly_miny - transform.f) / transform.e))
            c0 = max(0, int((poly_minx - transform.c) / transform.a))
            c1 = min(w - 1, int((poly_maxx - transform.c) / transform.a))

            if r0 > r1:
                r0, r1 = r1, r0
            if c0 > c1:
                c0, c1 = c1, c0

            valid_in_cell: list[float] = []
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if valid_mask[r, c]:
                        pt = Point(xs[r, c], ys[r, c])
                        if poly.contains(pt):
                            valid_in_cell.append(float(et_data[r, c]) * 0.1)

            if len(valid_in_cell) > 0:
                fallback_eligible_cells += 1
            else:
                unresolvable_cells += 1

    total_pop = direct_centroid_cells + fallback_eligible_cells
    total_null = unresolvable_cells

    print(f"  Centroid Sampling Results:")
    print(f"    - Direct valid centroid cells  : {direct_centroid_cells:,} ({direct_centroid_cells/len(cells)*100:.2f}%)")
    print(f"    - Urban (code 32762) centroid  : {urban_centroid_cells:,} ({urban_centroid_cells/len(cells)*100:.2f}%)")
    print(f"    - Other special code centroid  : {other_special_centroid_cells:,}")
    print(f"    - Outside raster / Nodata      : {nodata_centroid_cells:,}")
    print(f"\n  Within-Cell Polygon Fallback:")
    print(f"    - Fallback eligible cells      : {fallback_eligible_cells:,} ({fallback_eligible_cells/len(cells)*100:.2f}%)")
    print(f"    - Strict null retention cells  : {unresolvable_cells:,} ({unresolvable_cells/len(cells)*100:.2f}%)")
    print(f"\n  Projected Integration Coverage:")
    print(f"    - Total populated cells        : {total_pop:,} ({total_pop/len(cells)*100:.2f}%)")
    print(f"    - Total strict null cells      : {total_null:,} ({total_null/len(cells)*100:.2f}%)")

    if centroid_et_values:
        print(f"\n  Sampled Centroid ET Range:")
        print(f"    Min  : {min(centroid_et_values):.2f} mm/8day ({min(centroid_et_values)/8:.3f} mm/day)")
        print(f"    Max  : {max(centroid_et_values):.2f} mm/8day ({max(centroid_et_values)/8:.3f} mm/day)")
        print(f"    Mean : {np.mean(centroid_et_values):.2f} mm/8day ({np.mean(centroid_et_values)/8:.3f} mm/day)")


def main() -> None:
    print("=" * 72)
    print("  ROOTWISE M2: NASA MODIS MOD16A2GF ET RASTER INSPECTION")
    print("=" * 72)

    et_path = find_geotiff("*MOD16A2GF*ET_500m*") or find_geotiff("*MOD16A2GF*ET_*")
    qc_path = find_geotiff("*MOD16A2GF*ET_QC_500m*") or find_geotiff("*MOD16A2GF*ET_QC_*")

    if not et_path or not qc_path:
        print("\nGeoTIFF raster files for MOD16A2GF ET not found in data/raw/modis/.")
        print("Expected files:")
        print("  - MOD16A2GF.061__500m_8_days_ET_doy2016001000000_aid0001.tif")
        print("  - MOD16A2GF.061__500m_8_days_ET_QC_doy2016001000000_aid0001.tif")
        print("\nPlease follow the instructions in 'scripts/prepare_appeears_modis_et.py'")
        print("to submit the AppEEARS request and download the GeoTIFFs.")
        sys.exit(0)

    # 1. Inspect rasters
    et_dict = inspect_raster(et_path, "ET_500m (Total Evapotranspiration)")
    qc_dict = inspect_raster(qc_path, "ET_QC_500m (Quality Flags)")

    # 2. Check consistency
    print("\n--- Raster Alignment & Consistency Check ---")
    dims_match = (et_dict["width"] == qc_dict["width"]) and (et_dict["height"] == qc_dict["height"])
    crs_match = (et_dict["crs"] == qc_dict["crs"])
    bounds_match = (et_dict["bounds"] == qc_dict["bounds"])
    res_match = (et_dict["res"] == qc_dict["res"])

    print(f"  Dimensions Match  : {dims_match} ({et_dict['width']}x{et_dict['height']})")
    print(f"  CRS Match         : {crs_match} ({et_dict['crs']})")
    print(f"  Bounds Match      : {bounds_match}")
    print(f"  Resolution Match  : {res_match}")

    if not (dims_match and crs_match and bounds_match):
        print("\nWARNING: ET and QC rasters have mismatched spatial parameters!")
        sys.exit(1)

    # 3. Analyze ET data
    analyze_et(et_dict)

    # 4. Analyze QC data
    analyze_qc(qc_dict)

    # 5. Evaluate grid overlay
    evaluate_grid_coverage(et_dict, qc_dict)

    print("\n" + "=" * 72)
    print("  RASTER INSPECTION COMPLETED SUCCESSFULLY (READ-ONLY)")
    print("  No files were modified. Ready for integration when approved.")
    print("=" * 72)


if __name__ == "__main__":
    main()
