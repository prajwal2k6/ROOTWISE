"""
ROOTWISE M2 – Export Bengaluru Urban Boundary GeoJSON for NASA AppEEARS
=======================================================================
Extracts the official, validated Bengaluru Urban district boundary from
data/processed/boundaries/india_districts_cleaned.gpkg, reprojects it to
EPSG:4326 (WGS84), attaches standardized metadata (district, state, country),
and exports it to data/raw/modis/bengaluru_urban_boundary.geojson.

Performs strict validation against the 2,380 Bengaluru Urban grid cells.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parent.parent

GPKG_PATH = ROOT / "data/processed/boundaries/india_districts_cleaned.gpkg"
GRID_JSON_PATH = ROOT / "data/outputs/bengaluru_urban_20160101.json"
OUTPUT_DIR = ROOT / "data/raw/modis"
OUTPUT_GEOJSON = OUTPUT_DIR / "bengaluru_urban_boundary.geojson"


def main() -> None:
    print("=" * 70)
    print("  ROOTWISE M2: EXPORT BENGALURU URBAN BOUNDARY FOR APPEEARS")
    print("=" * 70)

    # 1. Verify source data
    if not GPKG_PATH.exists():
        raise FileNotFoundError(f"District boundaries GeoPackage not found at: {GPKG_PATH}")

    print(f"\n[1] Reading district boundary from: {GPKG_PATH.relative_to(ROOT)}")
    gdf = gpd.read_file(GPKG_PATH)

    # Filter strictly for Bengaluru Urban
    urban_mask = gdf["district"] == "Bengaluru Urban"
    if not urban_mask.any():
        raise ValueError("District 'Bengaluru Urban' not found in boundaries GeoPackage.")

    blr_row = gdf[urban_mask].iloc[0]
    print(f"    Found district: {blr_row['district']}")
    print(f"    State code    : {blr_row.get('stcode')} ({blr_row.get('state_name', 'Karnataka')})")
    print(f"    District code : {blr_row.get('dtcode')}")

    # Explicit check against Bengaluru Rural
    rural_mask = gdf["district"] == "Bengaluru Rural"
    if rural_mask.any():
        rural_row = gdf[rural_mask].iloc[0]
        print(f"    Confirmed separate Bengaluru Rural exists (dtcode={rural_row.get('dtcode')}) - NOT included.")

    # 2. Extract and reproject to EPSG:4326
    print("\n[2] Reprojecting geometry from EPSG:7755 to EPSG:4326 (WGS84)...")
    urban_gdf = gdf[urban_mask].to_crs("EPSG:4326").copy()
    geom = urban_gdf.geometry.iloc[0]

    # Validate geometry
    if geom.is_empty:
        raise ValueError("Bengaluru Urban geometry is EMPTY.")
    if not geom.is_valid:
        raise ValueError("Bengaluru Urban geometry is INVALID.")

    print(f"    Geometry type : {geom.geom_type}")
    print(f"    Valid geometry: {geom.is_valid}")
    print(f"    Non-empty     : {not geom.is_empty}")
    minx, miny, maxx, maxy = geom.bounds
    print(f"    WGS84 Bounds  : Lon [{minx:.6f}, {maxx:.6f}], Lat [{miny:.6f}, {maxy:.6f}]")

    # 3. Construct clean properties
    clean_props = {
        "district": "Bengaluru Urban",
        "state": str(blr_row.get("state_name", "Karnataka")),
        "state_code": str(blr_row.get("state", "KA")),
        "country": "India",
        "district_code": int(blr_row.get("dtcode", 525)),
        "state_numeric_code": int(blr_row.get("stcode", 29)),
        "source_agency": str(blr_row.get("src_agency", "Survey of India (SOI)")),
        "target_use": "NASA AppEEARS Area Request",
    }

    # Create export GeoDataFrame
    export_gdf = gpd.GeoDataFrame(
        [clean_props],
        geometry=[geom],
        crs="EPSG:4326",
    )

    # 4. Save to data/raw/modis/bengaluru_urban_boundary.geojson
    print(f"\n[3] Exporting to: {OUTPUT_GEOJSON.relative_to(ROOT)}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    export_gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    file_size_kb = OUTPUT_GEOJSON.stat().st_size / 1024
    print(f"    File saved successfully ({file_size_kb:.2f} KB)")

    # 5. Reopen and validate saved GeoJSON
    print(f"\n[4] Reopening and validating saved GeoJSON...")
    with OUTPUT_GEOJSON.open("r", encoding="utf-8") as f:
        reopened_json = json.load(f)

    if reopened_json.get("type") != "FeatureCollection":
        raise ValueError(f"Expected FeatureCollection, got {reopened_json.get('type')}")

    features = reopened_json.get("features", [])
    if len(features) != 1:
        raise ValueError(f"Expected exactly 1 feature, got {len(features)}")

    reopened_gdf = gpd.read_file(OUTPUT_GEOJSON)
    r_geom = reopened_gdf.geometry.iloc[0]
    r_crs = reopened_gdf.crs

    if r_crs.to_string() != "EPSG:4326":
        raise ValueError(f"Saved CRS mismatch: expected EPSG:4326, got {r_crs}")

    if not r_geom.is_valid or r_geom.is_empty:
        raise ValueError("Reopened geometry failed validity check.")

    r_props = reopened_gdf.iloc[0]
    for required_key in ["district", "state", "country"]:
        if required_key not in r_props:
            raise KeyError(f"Missing required property: '{required_key}'")

    print("    Reopened CRS          : EPSG:4326 (PASSED)")
    print("    Reopened Geometry     : Valid & non-empty (PASSED)")
    print(f"    District property     : {r_props['district']}")
    print(f"    State property        : {r_props['state']}")
    print(f"    Country property      : {r_props['country']}")

    # 6. Verify against the 2,380 grid cells in data/outputs/bengaluru_urban_20160101.json
    print(f"\n[5] Cross-verifying boundary against 2,380 grid cells...")
    if not GRID_JSON_PATH.exists():
        raise FileNotFoundError(f"Grid JSON not found at: {GRID_JSON_PATH}")

    with GRID_JSON_PATH.open("r", encoding="utf-8") as f:
        grid_data = json.load(f)

    cells = grid_data.get("cells", [])
    inside_count = 0
    intersects_count = 0

    for cell in cells:
        pt = Point(cell["centroid_lon"], cell["centroid_lat"])
        poly = shape(cell["geometry"])
        if r_geom.contains(pt):
            inside_count += 1
        elif r_geom.intersects(poly):
            intersects_count += 1

    covered_total = inside_count + intersects_count
    print(f"    Total cells tested    : {len(cells)}")
    print(f"    Centroids inside      : {inside_count} ({inside_count/len(cells)*100:.2f}%)")
    print(f"    Boundary intersecting : {intersects_count} ({intersects_count/len(cells)*100:.2f}%)")
    print(f"    Total cells covered   : {covered_total} / {len(cells)} (100.0%)")

    if covered_total != len(cells):
        raise ValueError(f"Boundary fails to cover all cells ({covered_total}/{len(cells)} covered).")

    print("\n" + "=" * 70)
    print("  ALL VALIDATIONS PASSED: Boundary ready for NASA AppEEARS")
    print("=" * 70)


if __name__ == "__main__":
    main()
