"""
ROOTWISE M2 – NASA POWER Integration
=====================================
Downloads T2M_MIN, T2M_MAX and RH2M from the NASA POWER Daily Regional API
for 2016-01-01 and integrates them into the Bengaluru Urban JSON dataset.

API endpoint : https://power.larc.nasa.gov/api/temporal/daily/regional
Bounding box : lon 76.5–79.5, lat 11.5–14.5  (3-degree span, satisfies the
               2-degree-minimum requirement)
Native res.  : ~0.5° × 0.625° (MERRA-2 reanalysis grid)

IMPORTANT LIMITATIONS
---------------------
• NASA POWER data are derived from MERRA-2 reanalysis at ~0.5° × 0.625°
  native resolution (≈ 55 km × 70 km at this latitude).
• Each 1 km grid cell is assigned the value of the single nearest POWER
  grid point with a valid, finite measurement.  Multiple cells may share
  the same source value.  No interpolation is performed.
• Values are estimates, not direct field measurements.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

import requests

# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT = Path(__file__).resolve().parent.parent

FULL_JSON     = ROOT / "data/outputs/bengaluru_urban_20160101.json"
SAMPLE_JSON   = ROOT / "data/outputs/bengaluru_urban_sample_3_cells.json"
RAW_POWER_DIR = ROOT / "data/raw/nasa_power"

DATA_DATE  = "2016-01-01"
START_DATE = "20160101"
END_DATE   = "20160101"

# Bounding box — satisfies the ≥ 2-degree requirement on each axis.
LAT_MIN, LAT_MAX = 11.5, 14.5
LON_MIN, LON_MAX = 76.5, 79.5

COMMUNITY = "AG"
FORMAT    = "JSON"

POWER_API_BASE = "https://power.larc.nasa.gov/api/temporal/daily/regional"

# Parameters fetched one at a time (requirement: separate downloads).
PARAMETERS: dict[str, str] = {
    "T2M_MIN": "temperature_min_c",
    "T2M_MAX": "temperature_max_c",
    "RH2M":    "humidity_pct",
}

POWER_NATIVE_RESOLUTION = "~0.5 × 0.625 degree (MERRA-2)"
TIMEOUT_SECONDS = 120

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


# ==========================================
# 2. PRE-FLIGHT: VALIDATE EXISTING JSON
# ==========================================

def validate_input_json(full_data: dict) -> None:
    """
    Verify the existing JSON is complete and consistent before any
    download or modification takes place.

    Checks (requirement 1):
      • Exactly EXPECTED_CELL_COUNT cells.
      • All grid IDs are unique non-empty strings.
      • Every cell has a finite centroid_lat in [-90, 90]
        and a finite centroid_lon in [-180, 180].
      • Every cell's indicators dict contains all required keys.
      • indicator_metadata contains all required keys.

    Raises ValueError on the first detected problem.
    """
    errors: list[str] = []

    cells = full_data.get("cells")
    if not isinstance(cells, list):
        raise ValueError("'cells' field is missing or not a list.")

    # --- Cell count ---
    if len(cells) != EXPECTED_CELL_COUNT:
        errors.append(
            f"Expected exactly {EXPECTED_CELL_COUNT} cells, "
            f"found {len(cells)}."
        )

    # --- Grid ID uniqueness and centroid validity ---
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
                errors.append(
                    f"{prefix}: indicators missing keys: {sorted(missing)}."
                )

    # --- Indicator metadata ---
    metadata = full_data.get("indicator_metadata")
    if not isinstance(metadata, dict):
        errors.append("'indicator_metadata' is missing or not a dict.")
    else:
        missing_meta = REQUIRED_METADATA_KEYS - metadata.keys()
        if missing_meta:
            errors.append(
                f"indicator_metadata missing keys: {sorted(missing_meta)}."
            )

    if errors:
        raise ValueError(
            "Pre-flight validation FAILED:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    print(
        f"  Pre-flight checks PASSED: "
        f"{len(cells)} cells, {len(seen_ids)} unique grid IDs, "
        f"all centroids and indicator fields present."
    )


# ==========================================
# 3. DOWNLOAD FROM NASA POWER API
# ==========================================

def download_parameter(param_name: str) -> dict:
    """
    Download a single NASA POWER parameter for the regional bounding box.
    Returns the parsed JSON response dict.
    Raises RuntimeError on HTTP error or JSON parse failure.
    """
    url_params = {
        "parameters":    param_name,
        "community":     COMMUNITY,
        "format":        FORMAT,
        "start":         START_DATE,
        "end":           END_DATE,
        "latitude-min":  LAT_MIN,
        "latitude-max":  LAT_MAX,
        "longitude-min": LON_MIN,
        "longitude-max": LON_MAX,
    }

    print(f"  Requesting {param_name} …", flush=True)

    resp = requests.get(
        POWER_API_BASE,
        params=url_params,
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": "ROOTWISE-M2/1.0 (NASA-hackathon)"},
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"NASA POWER API returned HTTP {resp.status_code} for "
            f"{param_name}.\n"
            f"Response (first 500 chars): {resp.text[:500]}"
        )

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse NASA POWER response for {param_name}: {exc}\n"
            f"Raw text (first 500 chars): {resp.text[:500]}"
        ) from exc

    return data


# ==========================================
# 4. SAVE RAW RESPONSES
# ==========================================

def save_raw(param_name: str, data: dict) -> Path:
    RAW_POWER_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RAW_POWER_DIR / f"nasa_power_{param_name}_{START_DATE}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved raw response → {out_file.relative_to(ROOT)}")
    return out_file


# ==========================================
# 5. EXTRACT POWER GRID POINTS FROM GEOJSON
# ==========================================

def extract_power_points(data: dict, param_name: str) -> list[dict]:
    """
    Parse the NASA POWER GeoJSON FeatureCollection.

    Confirmed NASA POWER /regional JSON structure (from live response):
      Top level  : { "type": "FeatureCollection", "features": [...], … }
      Per feature: {
          "geometry": { "coordinates": [lon, lat, elevation] },
          "properties": {
              "parameter": {
                  "<PARAM_NAME>": { "<YYYYMMDD>": <value> }
              }
          }
      }

    Fill value: NASA POWER uses -999 for missing data.
    Points whose value resolves to None (fill value, non-numeric, or absent)
    are retained in the list so callers can skip them in matching.

    Returns a list of dicts:
      { "lon": float, "lat": float, "value": float | None }
    """
    # Locate the FeatureCollection (handles both top-level and nested).
    fc: dict | None = None

    if data.get("type") == "FeatureCollection":
        fc = data
    elif "features" in data and isinstance(data["features"], list):
        fc = data
    else:
        for val in data.values():
            if isinstance(val, dict) and val.get("type") == "FeatureCollection":
                fc = val
                break

    if fc is None or "features" not in fc:
        raise RuntimeError(
            f"Cannot locate FeatureCollection in NASA POWER response "
            f"for {param_name}.\n"
            f"Top-level keys: {list(data.keys())}"
        )

    features = fc["features"]
    if not isinstance(features, list) or len(features) == 0:
        raise RuntimeError(
            f"No features found in NASA POWER response for {param_name}."
        )

    points: list[dict] = []

    for feat in features:
        coords = feat.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])

        props = feat.get("properties", {})

        # Actual structure: properties → "parameter" → { PARAM_NAME: { DATE: val } }
        param_block = props.get("parameter", props)  # fall back to props itself

        param_values = param_block.get(param_name)
        if param_values is None:
            # Case-insensitive fallback.
            for k, v in param_block.items():
                if k.upper() == param_name.upper():
                    param_values = v
                    break

        value: float | None = None
        if isinstance(param_values, dict):
            raw_val = param_values.get(START_DATE)
            if raw_val is not None:
                try:
                    fv = float(raw_val)
                    # Reject NASA POWER fill values (≤ -900).
                    if math.isfinite(fv) and fv > -900:
                        value = round(fv, 4)
                except (ValueError, TypeError):
                    pass

        points.append({"lon": lon, "lat": lat, "value": value})

    if not points:
        raise RuntimeError(
            f"Zero POWER grid points parsed for {param_name}."
        )

    valid_count = sum(1 for p in points if p["value"] is not None)
    print(
        f"  Parsed {len(points)} POWER grid points for {param_name} "
        f"({valid_count} with valid values, "
        f"{len(points) - valid_count} fill/missing)."
    )
    return points


# ==========================================
# 6. VALIDATE DOWNLOADED POWER VALUES
# ==========================================

def validate_power_values(power_data: dict[str, list[dict]]) -> None:
    """
    Domain validation of downloaded POWER values (requirement 3).

    Checks:
      • RH2M:    every non-None value must satisfy 0 ≤ value ≤ 100.
      • T2M_MIN: every non-None value must be finite.
      • T2M_MAX: every non-None value must be finite.
      • For every POWER grid point where both T2M_MIN and T2M_MAX are
        non-None, T2M_MIN must not exceed T2M_MAX.

    Raises ValueError listing all violations found.
    """
    errors: list[str] = []

    # --- RH2M range check ---
    for pt in power_data.get("RH2M", []):
        v = pt["value"]
        if v is None:
            continue
        if not (0.0 <= v <= 100.0):
            errors.append(
                f"RH2M out of range [0, 100]: {v} at "
                f"(lat={pt['lat']}, lon={pt['lon']})."
            )

    # --- T2M_MIN finite check ---
    for pt in power_data.get("T2M_MIN", []):
        v = pt["value"]
        if v is None:
            continue
        if not math.isfinite(v):
            errors.append(
                f"T2M_MIN is not finite: {v} at "
                f"(lat={pt['lat']}, lon={pt['lon']})."
            )

    # --- T2M_MAX finite check ---
    for pt in power_data.get("T2M_MAX", []):
        v = pt["value"]
        if v is None:
            continue
        if not math.isfinite(v):
            errors.append(
                f"T2M_MAX is not finite: {v} at "
                f"(lat={pt['lat']}, lon={pt['lon']})."
            )

    # --- T2M_MIN ≤ T2M_MAX per matched location ---
    # Build lookup: (lat, lon) → value for each parameter.
    def _build_lookup(points: list[dict]) -> dict[tuple[float, float], float | None]:
        return {(p["lat"], p["lon"]): p["value"] for p in points}

    min_lookup = _build_lookup(power_data.get("T2M_MIN", []))
    max_lookup = _build_lookup(power_data.get("T2M_MAX", []))

    shared_keys = min_lookup.keys() & max_lookup.keys()
    for key in sorted(shared_keys):
        t_min = min_lookup[key]
        t_max = max_lookup[key]
        if t_min is None or t_max is None:
            continue
        if t_min > t_max:
            errors.append(
                f"T2M_MIN ({t_min}) > T2M_MAX ({t_max}) at "
                f"(lat={key[0]}, lon={key[1]})."
            )

    if errors:
        raise ValueError(
            "Downloaded POWER value validation FAILED:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    print("  Downloaded value validation PASSED (RH2M range, T2M finite, MIN ≤ MAX).")


# ==========================================
# 7. NEAREST-POINT MATCHING
# ==========================================

def _approx_sq_dist(lat1: float, lon1: float,
                    lat2: float, lon2: float) -> float:
    """
    Approximate squared angular distance in degrees², corrected for
    longitude compression at the mean latitude.  Sufficient for
    nearest-point matching over the small, coarse POWER grid.
    """
    dlat = lat2 - lat1
    dlon = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2.0))
    return dlat * dlat + dlon * dlon


def match_to_nearest(
    centroid_lat: float,
    centroid_lon: float,
    power_points: list[dict],
) -> float | None:
    """
    Return the value of the nearest POWER grid point that has a
    non-None, finite value (requirement 2).

    Points with value=None or non-finite value are skipped entirely.
    Returns None only when no valid POWER point exists in the list.
    No interpolation is performed.
    """
    best_val: float | None = None
    best_dist = float("inf")

    for pt in power_points:
        v = pt["value"]
        # Skip points with no usable measurement.
        if v is None or not math.isfinite(v):
            continue
        d = _approx_sq_dist(centroid_lat, centroid_lon, pt["lat"], pt["lon"])
        if d < best_dist:
            best_dist = d
            best_val = v

    return best_val


# ==========================================
# 8. BACKUP EXISTING JSON
# ==========================================

def create_backup() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = FULL_JSON.with_name(
        f"{FULL_JSON.stem}_backup_{timestamp}{FULL_JSON.suffix}"
    )
    shutil.copy2(FULL_JSON, backup)
    print(f"  Backup created → {backup.relative_to(ROOT)}")
    return backup


# ==========================================
# 9. LOAD EXISTING JSON
# ==========================================

def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ==========================================
# 10. UPDATE CELLS WITH POWER VALUES
# ==========================================

def update_cells(
    cells: list[dict],
    power_data: dict[str, list[dict]],
) -> dict[str, dict[str, int]]:
    """
    For each cell, find the nearest valid POWER point and update only
    the three target indicator keys.

    Preserved without modification (requirement 4):
      • rainfall_mm
      • geometry, grid_id, state, district, centroid_lat, centroid_lon
      • CRS, observation date (top-level fields, not touched here)
      • all other indicators not in PARAMETERS.values()

    Returns summary counts: { indicator_key: {"filled": int, "null": int} }
    """
    counts: dict[str, dict[str, int]] = {
        ind: {"filled": 0, "null": 0} for ind in PARAMETERS.values()
    }

    for cell in cells:
        lat = cell["centroid_lat"]
        lon = cell["centroid_lon"]
        indicators = cell["indicators"]

        for param_name, indicator_key in PARAMETERS.items():
            power_points = power_data[param_name]
            value = match_to_nearest(lat, lon, power_points)

            # Only the three target keys are written.
            indicators[indicator_key] = value

            if value is not None:
                counts[indicator_key]["filled"] += 1
            else:
                counts[indicator_key]["null"] += 1

    return counts


# ==========================================
# 11. UPDATE INDICATOR METADATA
# ==========================================

def update_metadata(indicator_metadata: dict) -> None:
    """
    Update metadata for the three POWER-sourced indicators only.
    All other indicator_metadata entries are left unchanged.
    """
    _note = (
        "Coarse reanalysis estimate (MERRA-2). "
        "Each 1 km grid cell is assigned the value of the nearest POWER "
        "grid point with a valid measurement. "
        "Multiple cells may share the same source value. "
        "No interpolation is performed."
    )

    indicator_metadata["temperature_min_c"] = {
        "source":            "NASA POWER MERRA-2 (T2M_MIN)",
        "units":             "degree Celsius",
        "status":            "estimated",
        "native_resolution": POWER_NATIVE_RESOLUTION,
        "assignment_method": "nearest valid POWER grid point",
        "note":              _note,
    }

    indicator_metadata["temperature_max_c"] = {
        "source":            "NASA POWER MERRA-2 (T2M_MAX)",
        "units":             "degree Celsius",
        "status":            "estimated",
        "native_resolution": POWER_NATIVE_RESOLUTION,
        "assignment_method": "nearest valid POWER grid point",
        "note":              _note,
    }

    indicator_metadata["humidity_pct"] = {
        "source":            "NASA POWER MERRA-2 (RH2M)",
        "units":             "%",
        "status":            "estimated",
        "native_resolution": POWER_NATIVE_RESOLUTION,
        "assignment_method": "nearest valid POWER grid point",
        "note":              _note,
    }


# ==========================================
# 12. SAVE JSON SAFELY (temp-then-rename)
# ==========================================

def save_json_safe(path: Path, content: dict) -> None:
    """
    Write content to a temporary file, then atomically rename it to path.
    If any error occurs, the .tmp file is removed and path is never touched
    (requirement 6).
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, allow_nan=False)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
    print(
        f"  Saved → {path.relative_to(ROOT)}  "
        f"({round(path.stat().st_size / 1024 / 1024, 2)} MB)"
    )


# ==========================================
# 13. REGENERATE THREE-CELL SAMPLE
# ==========================================

def regenerate_sample(full_data: dict) -> None:
    """Rebuild the sample JSON from the first three cells of the updated data."""
    sample = {k: v for k, v in full_data.items() if k != "cells"}
    sample["cells"] = full_data["cells"][:3]
    if len(sample["cells"]) != 3:
        raise ValueError(
            "Cannot create three-cell sample – fewer than 3 cells present."
        )
    save_json_safe(SAMPLE_JSON, sample)


# ==========================================
# 14. MAIN PIPELINE
# ==========================================

def main() -> None:
    print("\n========== ROOTWISE M2 – NASA POWER INTEGRATION ==========")

    # ── Preflight: file existence ──────────────────────────────────────
    if not FULL_JSON.exists():
        sys.exit(f"ERROR: Full JSON not found: {FULL_JSON}")

    # ── Step 1: Load and validate existing JSON ────────────────────────
    print("\n[1] Loading and validating existing JSON …")
    full_data = load_json(FULL_JSON)
    cells     = full_data["cells"]
    print(f"    Cells loaded: {len(cells)}")

    # Structural checks before anything else.
    if full_data.get("crs") != "EPSG:4326":
        sys.exit(f"ERROR: CRS mismatch – expected EPSG:4326, "
                 f"got {full_data.get('crs')!r}.")
    if full_data.get("data_date") != DATA_DATE:
        sys.exit(f"ERROR: Date mismatch – expected {DATA_DATE}, "
                 f"got {full_data.get('data_date')!r}.")

    # Detailed pre-flight validation (requirement 1).
    validate_input_json(full_data)

    # ── Step 2: Create backup BEFORE any modification ──────────────────
    # Backup happens before downloads too, so the original is safe even
    # if a network error occurs mid-run (requirement 5).
    print("\n[2] Creating backup …")
    backup_path = create_backup()

    # ── Step 3: Download POWER data ────────────────────────────────────
    print("\n[3] Downloading NASA POWER parameters (one per request) …")
    power_data: dict[str, list[dict]] = {}

    for param_name in PARAMETERS:
        print(f"\n  Parameter: {param_name}")
        raw = download_parameter(param_name)
        save_raw(param_name, raw)
        power_data[param_name] = extract_power_points(raw, param_name)

    # ── Step 4: Validate downloaded values ────────────────────────────
    print("\n[4] Validating downloaded POWER values …")
    validate_power_values(power_data)

    # ── Steps 5–7: Update cells, metadata, save ───────────────────────
    # All writes are inside a try/except so the original file is never
    # partially overwritten on failure (requirement 6).
    print("\n[5] Matching grid centroids to nearest valid POWER points …")
    try:
        counts = update_cells(cells, power_data)

        for indicator_key, c in counts.items():
            print(f"    {indicator_key}: {c['filled']} filled, {c['null']} null")

        print("\n[6] Updating indicator_metadata …")
        update_metadata(full_data["indicator_metadata"])

        print("\n[7] Saving updated full JSON …")
        save_json_safe(FULL_JSON, full_data)

        print("\n[8] Regenerating three-cell sample …")
        regenerate_sample(full_data)

    except Exception as exc:
        print(
            f"\nERROR during processing: {exc}\n"
            f"Original JSON was NOT overwritten.  "
            f"Backup is at: {backup_path}"
        )
        sys.exit(1)

    # ── Summary ────────────────────────────────────────────────────────
    print("\n========== INTEGRATION SUMMARY ==========")
    print(f"  Observation date  : {DATA_DATE}")
    print(f"  Bounding box      : lat {LAT_MIN}–{LAT_MAX}, lon {LON_MIN}–{LON_MAX}")
    print(f"  POWER resolution  : {POWER_NATIVE_RESOLUTION}")
    print(f"  Total cells       : {len(cells)}")
    for param_name, indicator_key in PARAMETERS.items():
        c = counts[indicator_key]
        print(
            f"  {param_name:10s} → {indicator_key}: "
            f"{c['filled']} filled, {c['null']} null"
        )
    print(f"  Backup            : {backup_path.name}")
    print(f"  Full JSON         : {FULL_JSON.relative_to(ROOT)}")
    print(f"  Sample JSON       : {SAMPLE_JSON.relative_to(ROOT)}")
    print(f"  Raw POWER files   : {RAW_POWER_DIR.relative_to(ROOT)}")
    print("\nNASA POWER integration completed successfully.")
    print("Run scripts/validate_bengaluru_json.py to verify the output.")


if __name__ == "__main__":
    main()
