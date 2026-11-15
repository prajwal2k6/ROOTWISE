"""
ROOTWISE M2 – NASA AppEEARS Request Preparer for MODIS Evapotranspiration
========================================================================
Prepares and optionally submits the NASA AppEEARS Area Request for
MODIS MOD16A2GF.061 (8-day, 500m gap-filled evapotranspiration) covering
Bengaluru Urban for the composite period 2016-01-01 to 2016-01-08.

Layers:
- ET_500m     (Total Evapotranspiration, kg/m^2/8day, scale factor 0.1)
- ET_QC_500m  (Evapotranspiration Quality Control flags, bit field)

Output Format: GeoTIFF
Output Projection: Geographic WGS84 (EPSG:4326)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_MODIS = ROOT / "data/raw/modis"
BOUNDARY_GEOJSON = RAW_MODIS / "bengaluru_urban_boundary.geojson"
PAYLOAD_JSON = RAW_MODIS / "appeears_et_request_payload.json"

APPEEARS_API_BASE = "https://appeears.earthdatacloud.nasa.gov/api"
PRODUCT = "MOD16A2GF.061"
LAYERS = ["ET_500m", "ET_QC_500m"]
START_DATE = "01-01-2016"
END_DATE = "01-08-2016"
TASK_NAME = "ROOTWISE_M2_MOD16A2GF_ET_20160101"


def build_payload(geojson_path: Path) -> dict[str, Any]:
    if not geojson_path.exists():
        raise FileNotFoundError(f"Boundary GeoJSON not found at: {geojson_path}")

    with geojson_path.open("r", encoding="utf-8") as f:
        geo_data = json.load(f)

    payload = {
        "task_type": "area",
        "task_name": TASK_NAME,
        "params": {
            "dates": [
                {
                    "startDate": START_DATE,
                    "endDate": END_DATE,
                }
            ],
            "layers": [
                {"product": PRODUCT, "layer": layer}
                for layer in LAYERS
            ],
            "output": {
                "format": {"type": "geotiff"},
                "projection": "geographic",
            },
            "geo": geo_data,
        },
    }
    return payload


def get_auth_token(user_token: str | None = None) -> str | None:
    if user_token:
        return user_token
    for env_var in ("APPEEARS_TOKEN", "EARTHDATA_TOKEN"):
        if env_var in os.environ and os.environ[env_var].strip():
            return os.environ[env_var].strip()
    return None


def submit_task(payload: dict[str, Any], token: str) -> dict[str, Any]:
    url = f"{APPEEARS_API_BASE}/task"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    if response.status_code != 202 and response.status_code != 200:
        raise RuntimeError(
            f"Task submission failed ({response.status_code}): {response.text}"
        )
    return response.json()


def check_task_status(task_id: str, token: str) -> dict[str, Any]:
    url = f"{APPEEARS_API_BASE}/task/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to check task status ({response.status_code}): {response.text}"
        )
    return response.json()


def download_bundle(task_id: str, token: str, output_dir: Path) -> list[Path]:
    bundle_url = f"{APPEEARS_API_BASE}/bundle/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    bundle_resp = requests.get(bundle_url, headers=headers, timeout=30)
    if bundle_resp.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch bundle info ({bundle_resp.status_code}): {bundle_resp.text}"
        )

    bundle_data = bundle_resp.json()
    files = bundle_data.get("files", [])
    downloaded: list[Path] = []

    print(f"\nTask completed! Downloading {len(files)} files to {output_dir}...")
    for item in files:
        file_id = item.get("file_id")
        file_name = item.get("file_name")
        file_size = item.get("file_size", 0)

        # Only download GeoTIFFs and metadata
        if not file_name.endswith((".tif", ".json", ".xml")):
            continue

        target_path = output_dir / file_name
        print(f"  Downloading {file_name} ({file_size / 1024:.1f} KB)...", end="", flush=True)

        download_url = f"{APPEEARS_API_BASE}/bundle/{task_id}/{file_id}"
        with requests.get(download_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(target_path, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=8192):
                    f_out.write(chunk)

        print(" Done!")
        downloaded.append(target_path)

    return downloaded


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare and submit NASA AppEEARS Area Request for MODIS ET."
    )
    parser.add_argument("--token", help="AppEEARS Bearer token for automated submission")
    parser.add_argument("--submit", action="store_true", help="Submit task if token is available")
    parser.add_argument("--poll", action="store_true", help="Poll task until done and download")
    args = parser.parse_args()

    print("=" * 72)
    print("  ROOTWISE M2: NASA AppEEARS MODIS ET RETRIEVAL PREPARER")
    print("=" * 72)
    print(f"Product             : {PRODUCT}")
    print(f"Layers              : {', '.join(LAYERS)}")
    print(f"Date Range          : {START_DATE} to {END_DATE} (DOY 2016001)")
    print(f"Output Format       : GeoTIFF")
    print(f"Output Projection   : Geographic WGS84 (EPSG:4326)")
    print(f"Boundary Vector     : {BOUNDARY_GEOJSON.relative_to(ROOT)}")

    # 1. Build and save payload
    payload = build_payload(BOUNDARY_GEOJSON)
    with PAYLOAD_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    payload_size_kb = PAYLOAD_JSON.stat().st_size / 1024
    print(f"\n[1] Prepared Request Payload:")
    print(f"    Saved to        : {PAYLOAD_JSON.relative_to(ROOT)} ({payload_size_kb:.2f} KB)")
    print(f"    Task Name       : {TASK_NAME}")
    print(f"    GeoJSON Type    : {payload['params']['geo'].get('type')}")
    print(f"    Features Count  : {len(payload['params']['geo'].get('features', []))}")

    # 2. Check for token
    token = get_auth_token(args.token)

    if not token or not args.submit:
        print("\n" + "=" * 72)
        print("  STEP-BY-STEP NASA AppEEARS RETRIEVAL INSTRUCTIONS")
        print("=" * 72)
        print("Because Earthdata / AppEEARS requires authenticated user access,")
        print("you can submit this request via the official NASA AppEEARS Web UI:")
        print()
        print("1. Go to NASA AppEEARS: https://appeears.earthdatacloud.nasa.gov/")
        print("   Sign in with your Earthdata credentials.")
        print()
        print("2. Navigate to: Extract -> Area")
        print("   Or direct link: https://appeears.earthdatacloud.nasa.gov/task/area")
        print()
        print("3. Fill in the form:")
        print(f"   • Task Name  : {TASK_NAME}")
        print("   • Region of Interest (Vector File):")
        print(f"     Upload file: data/raw/modis/bengaluru_urban_boundary.geojson")
        print(f"   • Date Range : {START_DATE} to {END_DATE}")
        print(f"   • Product    : {PRODUCT} (Terra Net Evapotranspiration Gap-Filled 8-Day 500m)")
        print(f"   • Layers     : Select BOTH:")
        print(f"                  - ET_500m (Total Evapotranspiration)")
        print(f"                  - ET_QC_500m (Evapotranspiration Quality Control flags)")
        print(f"   • Output Options:")
        print(f"                  - File Format: GeoTIFF")
        print(f"                  - Projection : Geographic (WGS84 / EPSG:4326)")
        print()
        print("4. Click 'Submit'.")
        print("   AppEEARS will extract and reproject the rasters (typically 2–3 minutes).")
        print()
        print("5. Once completed, download the files into:")
        print(f"   {RAW_MODIS.relative_to(ROOT)}/")
        print("   The two required files are:")
        print("   - MOD16A2GF.061__500m_8_days_ET_doy2016001000000_aid0001.tif")
        print("   - MOD16A2GF.061__500m_8_days_ET_QC_doy2016001000000_aid0001.tif")
        print("   (Note: 'aid0001' or similar suffix assigned by AppEEARS)")
        print()
        print("6. Run the raster inspection script:")
        print("   python scripts/inspect_modis_et_rasters.py")
        print("=" * 72)
        return

    # Automated submission
    print("\n[2] Submitting request programmatically to NASA AppEEARS API...")
    try:
        task_info = submit_task(payload, token)
        task_id = task_info.get("task_id")
        task_status = task_info.get("status")
        print(f"    Task ID         : {task_id}")
        print(f"    Initial Status  : {task_status}")
    except Exception as exc:
        print(f"    ERROR submitting task: {exc}")
        sys.exit(1)

    if not args.poll:
        print("\nTask submitted successfully! Use --poll to wait and download automatically.")
        return

    print("\n[3] Polling task status...")
    while True:
        status_info = check_task_status(task_id, token)
        curr_status = status_info.get("status")
        print(f"    Status: {curr_status} ...", flush=True)
        if curr_status == "done":
            break
        elif curr_status in ("error", "cancelled", "expired"):
            print(f"    Task failed with status: {curr_status}")
            sys.exit(1)
        time.sleep(15)

    downloaded = download_bundle(task_id, token, RAW_MODIS)
    print(f"\nAll files saved. Run 'python scripts/inspect_modis_et_rasters.py' to inspect.")


if __name__ == "__main__":
    main()
