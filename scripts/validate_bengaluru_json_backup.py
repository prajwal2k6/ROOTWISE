
import json
from pathlib import Path

file = Path("data/outputs/bengaluru_urban_20160101.json")

with file.open("r", encoding="utf-8") as f:
    data = json.load(f)

# Check batch-level fields
required_batch_fields = {
    "schema_version", "source", "region",
    "data_date", "resolution_m", "cells"
}

assert required_batch_fields.issubset(data.keys())
assert data["schema_version"] == "1.0"
assert data["data_date"] == "2016-01-01"
assert data["resolution_m"] == 1000
assert len(data["cells"]) == 2380

# Check every cell
required_cell_fields = {
    "grid_id", "geometry", "centroid_lat",
    "centroid_lon", "indicators", "data_quality"
}

required_indicators = {
    "rainfall_mm", "soil_moisture_pct",
    "temperature_min_c", "temperature_max_c",
    "humidity_pct", "ndvi", "evapotranspiration_mm"
}

grid_ids = set()
valid_rainfall = 0

for cell in data["cells"]:
    assert required_cell_fields.issubset(cell.keys())
    assert cell["grid_id"] not in grid_ids, "Duplicate grid ID"
    grid_ids.add(cell["grid_id"])

    assert cell["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert cell["geometry"]["coordinates"]

    indicators = cell["indicators"]
    assert required_indicators.issubset(indicators.keys())

    rainfall = indicators["rainfall_mm"]

    if rainfall is not None:
        assert isinstance(rainfall, (int, float))
        assert rainfall >= 0
        valid_rainfall += 1

    assert cell["data_quality"] in (
        "observed", "estimated", "missing"
    )

print("========== JSON VALIDATION ==========")
print("JSON parsing: PASSED")
print("Batch structure: PASSED")
print("Cell count:", len(data["cells"]))
print("Unique grid IDs:", len(grid_ids))
print("Geometry checks: PASSED")
print("Indicator structure: PASSED")
print("Valid rainfall values:", valid_rainfall)
print("=====================================")
print("ALL VALIDATION CHECKS PASSED!")
