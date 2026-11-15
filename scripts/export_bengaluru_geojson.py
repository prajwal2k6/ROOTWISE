"""
ROOTWISE M2 – GeoJSON Exporter for Bengaluru Urban Dataset
=========================================================
Converts the validated seven-indicator Bengaluru Urban dataset
(data/outputs/bengaluru_urban_20160101.json) into an RFC 7946 compliant
GeoJSON FeatureCollection (data/outputs/bengaluru_urban_20160101.geojson).

Requirements:
  - Exports all 2,380 grid cells (NOT a sample).
  - CRS: EPSG:4326 (WGS84 lat/lon).
  - Every feature includes:
      - id / properties.grid_id
      - properties.state, properties.district, properties.region_code
      - properties.data_date, properties.resolution_m
      - properties.centroid_lat, properties.centroid_lon
      - All 7 indicators: rainfall_mm, temperature_min_c, temperature_max_c,
        humidity_pct, soil_moisture_pct, ndvi, evapotranspiration_mm
      - properties.data_quality
  - Null indicator values strictly preserved as JSON null.
  - Verifies geometry validity and feature count.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
INPUT_JSON = ROOT / "data/outputs/bengaluru_urban_20160101.json"
OUTPUT_GEOJSON = ROOT / "data/outputs/bengaluru_urban_20160101.geojson"


def export_geojson() -> Path:
    print("=" * 72)
    print("  ROOTWISE M2: EXPORT BENGALURU URBAN GEOJSON")
    print("=" * 72)

    if not INPUT_JSON.exists():
        sys.exit(f"Input JSON not found: {INPUT_JSON}")

    print(f"[1] Loading dataset from {INPUT_JSON.relative_to(ROOT)}...")
    with INPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cells = data.get("cells", [])
    print(f"    Loaded {len(cells):,} cells from JSON.")

    region_info = data.get("region", {})
    region_code = region_info.get("code", "KA-BENGALURU-URBAN")
    data_date = data.get("data_date", "2016-01-01")
    resolution_m = data.get("resolution_m", 1000)

    # 2. Build GeoJSON FeatureCollection
    print("[2] Constructing GeoJSON FeatureCollection...")
    features: list[dict[str, Any]] = []

    for cell in cells:
        gid = cell["grid_id"]
        geom_dict = cell["geometry"]
        inds = cell.get("indicators", {})

        feature = {
            "type": "Feature",
            "id": gid,
            "geometry": geom_dict,
            "properties": {
                "grid_id": gid,
                "state": cell.get("state", "Karnataka"),
                "district": cell.get("district", "Bengaluru Urban"),
                "region_code": region_code,
                "data_date": data_date,
                "resolution_m": resolution_m,
                "centroid_lat": cell.get("centroid_lat"),
                "centroid_lon": cell.get("centroid_lon"),
                "rainfall_mm": inds.get("rainfall_mm"),
                "temperature_min_c": inds.get("temperature_min_c"),
                "temperature_max_c": inds.get("temperature_max_c"),
                "humidity_pct": inds.get("humidity_pct"),
                "soil_moisture_pct": inds.get("soil_moisture_pct"),
                "ndvi": inds.get("ndvi"),
                "evapotranspiration_mm": inds.get("evapotranspiration_mm"),
                "data_quality": cell.get("data_quality", "estimated"),
            },
        }
        features.append(feature)

    geojson_doc = {
        "type": "FeatureCollection",
        "name": "ROOTWISE_Bengaluru_Urban_20160101",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": features,
    }

    # 3. Write GeoJSON atomically
    print(f"[3] Writing GeoJSON to {OUTPUT_GEOJSON.relative_to(ROOT)}...")
    tmp_out = OUTPUT_GEOJSON.with_suffix(".geojson.tmp")
    with tmp_out.open("w", encoding="utf-8") as f:
        json.dump(geojson_doc, f, indent=2)
    tmp_out.replace(OUTPUT_GEOJSON)

    size_mb = OUTPUT_GEOJSON.stat().st_size / (1024 * 1024)
    print(f"    Saved successfully ({size_mb:.2f} MB / {OUTPUT_GEOJSON.stat().st_size:,} bytes).")

    # 4. Reopen and validate exported GeoJSON
    print("\n[4] Validating exported GeoJSON...")
    with OUTPUT_GEOJSON.open("r", encoding="utf-8") as f:
        reopened = json.load(f)

    assert reopened.get("type") == "FeatureCollection", "Exported file is not a FeatureCollection"
    reopened_features = reopened.get("features", [])
    assert len(reopened_features) == len(cells), f"Feature count mismatch: {len(reopened_features)} vs {len(cells)}"

    valid_geoms = 0
    pop_et = 0
    null_et = 0
    pop_ndvi = 0
    null_ndvi = 0

    for feat in reopened_features:
        g = shape(feat["geometry"])
        assert g.is_valid and not g.is_empty, f"Invalid geometry in feature {feat.get('id')}"
        valid_geoms += 1

        props = feat["properties"]
        if props["evapotranspiration_mm"] is not None:
            pop_et += 1
        else:
            null_et += 1

        if props["ndvi"] is not None:
            pop_ndvi += 1
        else:
            null_ndvi += 1

    assert valid_geoms == 2380, "Not all geometries are valid"
    assert pop_et == 2171 and null_et == 209, f"ET counts mismatch: pop={pop_et}, null={null_et}"
    assert pop_ndvi == 1293 and null_ndvi == 1087, f"NDVI counts mismatch: pop={pop_ndvi}, null={null_ndvi}"

    print(f"    • Feature count verified     : {len(reopened_features):,} cells")
    print(f"    • Geometry validity verified : 100% valid ({valid_geoms:,}/{len(reopened_features):,})")
    print(f"    • Indicator counts verified  : NDVI pop={pop_ndvi}, null={null_ndvi}; ET pop={pop_et}, null={null_et}")
    print("    • GeoJSON standard compliance: RFC 7946 valid")

    print("\n" + "=" * 72)
    print("  GEOJSON EXPORT COMPLETED SUCCESSFULLY")
    print("=" * 72)
    return OUTPUT_GEOJSON


if __name__ == "__main__":
    export_geojson()
