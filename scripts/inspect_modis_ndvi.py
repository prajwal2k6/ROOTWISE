"""
ROOTWISE M2 – NASA MODIS MOD13Q1 NDVI Inspection Tool
=====================================================
Standalone read-only inspection script for MODIS/Terra MOD13Q1 Version 061
(250 m 16-Day L3 Global Sinusoidal Grid) for 2016-01-01.

Granule: MOD13Q1.A2016001.h25v07.061.2021343014649
Tile: h25v07 (covers 10N-20N, ~71.8E-82.1E, completely enclosing Bengaluru Urban)
Temporal Coverage: 2016-01-01 to 2016-01-16 (DOY 001-016)

This script is strictly READ-ONLY and does NOT modify any JSON file or project data.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = ROOT / "data/outputs/bengaluru_urban_20160101.json"
RAW_MODIS_DIR = ROOT / "data/raw/modis"

SHORT_NAME = "MOD13Q1"
VERSION = "061"
DATA_DATE = "2016-01-01"
DOY_STR = "A2016001"
TILE = "h25v07"
GRANULE_NAME = "MOD13Q1.A2016001.h25v07.061.2021343014649"
GRANULE_HDF_URL = (
    f"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/"
    f"MOD13Q1.061/{GRANULE_NAME}/{GRANULE_NAME}.hdf"
)
OPENDAP_BASE_URL = (
    f"https://opendap.earthdata.nasa.gov/collections/C1748066515-LPCLOUD/granules/{GRANULE_NAME}"
)

# MODIS Sinusoidal projection constants
R_EARTH = 6371007.181
TILE_SIZE = (2.0 * math.pi * R_EARTH) / 36.0  # ~1111950.5196666666 m
N_PIXELS = 4800  # 4800x4800 for 250m
PIXEL_SIZE = TILE_SIZE / N_PIXELS  # ~231.656358 m

# Tile h25v07 upper-left coordinate in meters
# h=25: x_min = -pi*R + 25*TILE_SIZE, x_max = -pi*R + 26*TILE_SIZE
# v=07: y_max = (9 - 7)*TILE_SIZE = 2*TILE_SIZE, y_min = 1*TILE_SIZE
X_MIN = -math.pi * R_EARTH + 25 * TILE_SIZE
X_MAX = -math.pi * R_EARTH + 26 * TILE_SIZE
Y_MAX = (9 - 7) * TILE_SIZE
Y_MIN = (9 - 8) * TILE_SIZE

# Bengaluru Urban geographic bounding box
BLR_LAT_MIN, BLR_LAT_MAX = 12.661, 13.231
BLR_LON_MIN, BLR_LON_MAX = 77.329, 77.833


def latlon_to_sinusoidal(lat: float, lon: float) -> tuple[float, float]:
    """Convert WGS84 lat/lon to MODIS Sinusoidal x/y in meters."""
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    x = R_EARTH * lon_rad * math.cos(lat_rad)
    y = R_EARTH * lat_rad
    return x, y


def sinusoidal_to_pixel(x: float, y: float) -> tuple[int, int]:
    """Convert Sinusoidal x/y in tile h25v07 to row/col pixel index (0..4799)."""
    col = int((x - X_MIN) / PIXEL_SIZE)
    row = int((Y_MAX - y) / PIXEL_SIZE)
    return row, col


def pixel_to_sinusoidal(row: int, col: int) -> tuple[float, float]:
    """Convert row/col index to Sinusoidal pixel center x/y in meters."""
    x = X_MIN + (col + 0.5) * PIXEL_SIZE
    y = Y_MAX - (row + 0.5) * PIXEL_SIZE
    return x, y


def sinusoidal_to_latlon(x: float, y: float) -> tuple[float, float]:
    """Convert MODIS Sinusoidal x/y to WGS84 lat/lon in degrees."""
    lat_rad = y / R_EARTH
    lat = math.degrees(lat_rad)
    cos_lat = math.cos(lat_rad)
    if abs(cos_lat) < 1e-10:
        lon = 0.0
    else:
        lon_rad = x / (R_EARTH * cos_lat)
        lon = math.degrees(lon_rad)
    return lat, lon


def main() -> None:
    print("=" * 70)
    print("  ROOTWISE M2: MODIS MOD13Q1 NDVI INSPECTION")
    print("=" * 70)
    print(f"Product             : {SHORT_NAME} Version {VERSION}")
    print(f"Granule ID          : {GRANULE_NAME}")
    print(f"Composite Dates     : 2016-01-01 to 2016-01-16 (16-day composite)")
    print(f"Sinusoidal Tile     : {TILE} (h=25, v=7)")
    print(f"Tile Sinusoidal X   : [{X_MIN:,.1f}, {X_MAX:,.1f}] m")
    print(f"Tile Sinusoidal Y   : [{Y_MIN:,.1f}, {Y_MAX:,.1f}] m")
    print(f"Tile Dimension      : {N_PIXELS} x {N_PIXELS} pixels (nominal 250 m)")
    print(f"Pixel Resolution    : {PIXEL_SIZE:.6f} m")

    # Bounding box in Sinusoidal coordinates
    b_x_min, b_y_min = latlon_to_sinusoidal(BLR_LAT_MIN, BLR_LON_MIN)
    b_x_max, b_y_max = latlon_to_sinusoidal(BLR_LAT_MAX, BLR_LON_MAX)
    # Note: longitude increases with x, latitude increases with y
    r_min, c_min = sinusoidal_to_pixel(b_x_min, b_y_max)
    r_max, c_max = sinusoidal_to_pixel(b_x_max, b_y_min)

    print("\n[1] Bengaluru Urban Bounding Box Mapping on Tile h25v07:")
    print(f"    Geographic bounds   : Lat [{BLR_LAT_MIN:.4f}, {BLR_LAT_MAX:.4f}] N, "
          f"Lon [{BLR_LON_MIN:.4f}, {BLR_LON_MAX:.4f}] E")
    print(f"    Tile pixel rows     : {r_min} to {r_max} (span: {r_max - r_min + 1} pixels)")
    print(f"    Tile pixel cols     : {c_min} to {c_max} (span: {c_max - c_min + 1} pixels)")
    total_bbox_pixels = (r_max - r_min + 1) * (c_max - c_min + 1)
    print(f"    Total MODIS pixels in district bounding box: {total_bbox_pixels:,}")

    # Check output JSON
    print("\n[2] Checking target JSON dataset:")
    if not OUTPUT_JSON.exists():
        sys.exit(f"Output JSON not found at {OUTPUT_JSON}")

    with OUTPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cells = data.get("cells", [])
    print(f"    Loaded cells from JSON: {len(cells):,}")
    print(f"    Target indicator      : 'ndvi' (currently: {cells[0]['indicators'].get('ndvi')})")

    # Ratio of MODIS 250m pixels to 1 km cells
    ratio = total_bbox_pixels / len(cells)
    print(f"    Estimated MODIS 250m pixels per 1 km cell: ~{ratio:.1f}x oversampling")

    print("\n[3] Variable & Quality Flag Specification:")
    print("    • NDVI Dataset        : '250m 16 days NDVI' (Int16, shape 4800x4800)")
    print("    • Scale Factor        : 0.0001 (NDVI = raw * 0.0001)")
    print("    • Valid Raw Range     : -2000 to 10000 (-0.20 to +1.00)")
    print("    • Fill Value          : -3000 (missing/masked)")
    print("    • Pixel Reliability   : '250m 16 days pixel reliability' (Int8, rank scale)")
    print("                            0 = Good Data (high quality)")
    print("                            1 = Marginal Data")
    print("                            2 = Snow/Ice")
    print("                            3 = Cloudy")
    print("                            -1 = Fill/No Data")
    print("    • Detailed VI Quality : '250m 16 days VI Quality' (UInt16, bit-packed)")
    print("                            Bits 0-1: 00 = Good Quality, 01 = Marginal")
    print("                            Bits 2-5: VI Usefulness (0000 = highest)")

    print("\n" + "=" * 70)
    print("  INSPECTION SETUP VERIFIED (READ-ONLY)")
    print("  Ready for MODIS NDVI granule retrieval and integration.")
    print("=" * 70)


if __name__ == "__main__":
    main()
