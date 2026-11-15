"""
ROOTWISE M2 – SMAP PM Soil Moisture Inspection Tool
===================================================
Standalone read-only script to inspect the PM pass of SMAP SPL3SMP V009
for 2016-01-01 using an interactive Earthdata session in your local terminal.

This script does NOT modify any JSON file or project data.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

import earthaccess
import numpy as np
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = ROOT / "data/outputs/bengaluru_urban_20160101.json"
RAW_SMAP_DIR = ROOT / "data/raw/smap"

DATA_DATE = "2016-01-01"
SHORT_NAME = "SPL3SMP"
GROUP_NAME = "Soil_Moisture_Retrieval_Data_PM"

# Pre-identified exact granule (bypasses CMR catalogue search)
KNOWN_GRANULE_NAME = "SMAP_L3_SM_P_20160101_R19240_001.h5"
KNOWN_GRANULE_URL = (
    "https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/"
    "SMAP/SPL3SMP/009/2016/01/SMAP_L3_SM_P_20160101_R19240_001.h5"
)
KNOWN_VERSION = "009"
EXPECTED_PAYLOAD_MB = 32.28

BLR_LAT_MIN, BLR_LAT_MAX = 12.661, 13.231
BLR_LON_MIN, BLR_LON_MAX = 77.329, 77.833


def approx_sq_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = lat2 - lat1
    dlon = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2.0))
    return dlat * dlat + dlon * dlon


def download_granule_direct(session, url: str, target_path: Path, max_retries: int = 3) -> Path:
    """Download the known SMAP granule directly from NASA NSIDC using the authenticated
    session, bypassing CMR search entirely. Implements connection/read timeouts,
    exponential-backoff retries, and temporary file staging.
    """
    if target_path.exists() and target_path.stat().st_size > 30 * 1024 * 1024:
        print(f"    Using existing local granule: {target_path.name} ({target_path.stat().st_size / (1024 * 1024):.2f} MB)")
        return target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")

    print(f"    Downloading {KNOWN_GRANULE_NAME} directly from NASA NSIDC...")
    print(f"    Expected size: ~{EXPECTED_PAYLOAD_MB:.2f} MB")

    for attempt in range(1, max_retries + 1):
        try:
            # 15s connection timeout, 60s read timeout per chunk
            with session.get(url, stream=True, allow_redirects=True, timeout=(15, 60)) as resp:
                resp.raise_for_status()
                total_bytes = int(resp.headers.get("content-length", 0))
                downloaded_bytes = 0
                chunk_size = 1024 * 1024  # 1 MB

                with temp_path.open("wb") as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            if total_bytes > 0:
                                pct = (downloaded_bytes / total_bytes) * 100
                                cur_mb = downloaded_bytes / (1024 * 1024)
                                tot_mb = total_bytes / (1024 * 1024)
                                print(f"\r    Progress: {cur_mb:.1f} / {tot_mb:.1f} MB ({pct:.1f}%)", end="", flush=True)

                print()

                # Validate downloaded file size
                if temp_path.stat().st_size < 30 * 1024 * 1024:
                    raise IOError(f"Incomplete download ({temp_path.stat().st_size} bytes, expected > 30 MB)")

                temp_path.replace(target_path)
                print(f"    Download complete: {target_path.name} ({target_path.stat().st_size / (1024 * 1024):.2f} MB)")
                return target_path

        except Exception as exc:
            if temp_path.exists():
                temp_path.unlink()
            print(f"\n    [Attempt {attempt}/{max_retries}] Download failed: {exc}")
            if attempt < max_retries:
                wait_sec = attempt * 3
                print(f"    Retrying in {wait_sec} seconds...")
                time.sleep(wait_sec)
            else:
                raise RuntimeError(f"Failed to download granule after {max_retries} attempts: {exc}") from exc


def main() -> None:
    print("=" * 70)
    print("  ROOTWISE M2: SMAP SPL3SMP PM Group Inspection")
    print("=" * 70)

    local_path = RAW_SMAP_DIR / KNOWN_GRANULE_NAME

    # 1. Check if granule is already cached locally, otherwise authenticate and download
    if local_path.exists() and local_path.stat().st_size > 30 * 1024 * 1024:
        print(f"\n[1] Using existing local granule: {local_path.name} ({local_path.stat().st_size / (1024 * 1024):.2f} MB)")
        print("    No network download or authentication required.")
    else:
        print("\n[1] Authenticating with NASA Earthdata for download...")
        auth = earthaccess.login(strategy="interactive", persist=False)
        if not auth.authenticated:
            sys.exit("Authentication failed. Please verify your credentials and retry.")
        print("    Authentication: SUCCESSFUL")

        session = earthaccess.get_requests_https_session()
        print(f"\n[2] Downloading known granule directly from NASA NSIDC...")
        print(f"    Granule Name : {KNOWN_GRANULE_NAME}")
        print(f"    Collection   : {SHORT_NAME} Version {KNOWN_VERSION}")
        print(f"    Expected Size: ~{EXPECTED_PAYLOAD_MB:.2f} MB")
        local_path = download_granule_direct(session, KNOWN_GRANULE_URL, local_path)

    # 2. Open HDF5 with netCDF4 and inspect Soil_Moisture_Retrieval_Data_PM
    print(f"\n[2] Inspecting group '{GROUP_NAME}' with netCDF4...")
    with Dataset(local_path, "r") as nc:
        if GROUP_NAME not in nc.groups:
            sys.exit(f"Group '{GROUP_NAME}' not found in HDF5 file!")

        grp = nc.groups[GROUP_NAME]
        available_vars = list(grp.variables.keys())
        print(f"    Variables available in group: {len(available_vars)}")

        lat_var = grp.variables["latitude_pm"]
        lon_var = grp.variables["longitude_pm"]
        sm_var = grp.variables["soil_moisture_pm"]
        qf_var = grp.variables["retrieval_qual_flag_pm"]

        lats = np.array(lat_var[:], dtype=float)
        lons = np.array(lon_var[:], dtype=float)
        sm = np.array(sm_var[:], dtype=float)
        qf = np.array(qf_var[:], dtype=np.int32)

    print(f"    Grid dimensions: {sm.shape} (rows x cols)")

    # 3. Apply strict quality mask and documented range validation
    print("\n[3] Applying strict 3-bit quality mask and range validation:")
    print("    - (retrieval_qual_flag_pm & 0b111) == 0  [Bits 0, 1, 2 must all be 0]")
    print("    - soil_moisture_pm != -9999.0 and soil_moisture_pm > -900.0")
    print("    - math.isfinite(soil_moisture_pm)")
    print("    - Documented valid range: 0.02 <= soil_moisture_pm <= 0.50 m3/m3")

    coord_valid = (lats > -900.0) & (lons > -900.0)
    qf_valid = (qf & 0b111) == 0
    sm_valid = (sm > -900.0) & np.isfinite(sm) & (sm >= 0.02) & (sm <= 0.50)

    strict_valid_mask = coord_valid & qf_valid & sm_valid

    total_grid_pixels = sm.size
    total_valid_global = int(np.sum(strict_valid_mask))
    print(f"    Total global grid cells: {total_grid_pixels:,}")
    print(f"    Global valid recommended pixels: {total_valid_global:,}")

    # 4. Extract valid pixels near and over Bengaluru Urban
    # Regional bounding box: 11.5N to 14.5N, 76.5E to 79.5E
    regional_mask = (
        strict_valid_mask
        & (lats >= 11.5) & (lats <= 14.5)
        & (lons >= 76.5) & (lons <= 79.5)
    )
    reg_count = int(np.sum(regional_mask))
    print(f"\n[4] Regional pixels passing strict mask [11.5-14.5N, 76.5-79.5E]: {reg_count}")

    reg_lats = lats[regional_mask]
    reg_lons = lons[regional_mask]
    reg_sm = sm[regional_mask]
    reg_qf = qf[regional_mask]

    for i in range(reg_count):
        print(
            f"    Pixel {i+1}: lat={reg_lats[i]:.4f}, lon={reg_lons[i]:.4f}, "
            f"SM={reg_sm[i]:.4f} m3/m3 ({reg_sm[i]*100:.2f}%), "
            f"qual_flag={reg_qf[i]} (bin={bin(reg_qf[i])})"
        )

    # Bengaluru Urban exact box: 12.5 to 13.5N, 77.0 to 78.2E
    blr_mask = (
        strict_valid_mask
        & (lats >= 12.5) & (lats <= 13.5)
        & (lons >= 77.0) & (lons <= 78.2)
    )
    blr_count = int(np.sum(blr_mask))
    print(f"\n    Pixels directly over Bengaluru Urban [12.5-13.5N, 77.0-78.2E]: {blr_count}")

    # 6. Match to the 2,380 Bengaluru Urban grid cells
    print(f"\n[6] Simulating nearest-pixel matching to 2,380 grid cells from {OUTPUT_JSON.name}...")
    if not OUTPUT_JSON.exists():
        sys.exit(f"Output JSON not found at: {OUTPUT_JSON}")

    with OUTPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cells = data["cells"]
    print(f"    Loaded cells: {len(cells)}")

    if reg_count == 0:
        print("    WARNING: Zero valid SMAP pixels in regional box.")
        print("    Result: All 2,380 cells will remain null.")
        return

    # Build valid points pool
    valid_points = [
        {"lat": float(reg_lats[i]), "lon": float(reg_lons[i]), "sm": float(reg_sm[i])}
        for i in range(reg_count)
    ]

    assignments = {}
    matched_values = []

    for cell in cells:
        c_lat = cell["centroid_lat"]
        c_lon = cell["centroid_lon"]

        best_pt = None
        best_d = float("inf")
        for pt in valid_points:
            d = approx_sq_dist(c_lat, c_lon, pt["lat"], pt["lon"])
            if d < best_d:
                best_d = d
                best_pt = pt

        pt_key = (round(best_pt["lat"], 4), round(best_pt["lon"], 4))
        assignments[pt_key] = assignments.get(pt_key, 0) + 1
        matched_values.append(round(best_pt["sm"] * 100, 4))

    print(f"\n[7] Matching Results for 2,380 Bengaluru Urban Cells:")
    print(f"    Unique source SMAP pixels assigned: {len(assignments)}")
    for (plat, plon), count in assignments.items():
        pt_sm = [p["sm"] for p in valid_points if round(p["lat"], 4) == plat and round(p["lon"], 4) == plon][0]
        pct = pt_sm * 100
        print(
            f"    - Source Pixel (lat={plat:.4f}, lon={plon:.4f}): "
            f"SM={pt_sm:.4f} m3/m3 ({pct:.2f}%) -> Assigned to {count:,} cells ({count/len(cells)*100:.1f}%)"
        )

    print("\n" + "=" * 70)
    print("  INSPECTION COMPLETE (READ-ONLY)")
    print("  No project JSON files were modified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
