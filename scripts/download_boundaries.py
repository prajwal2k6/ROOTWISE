
import requests
import zipfile
from pathlib import Path

# Official NWIC district boundary GeoJSON download
url = (
    "https://nwdp.nwic.gov.in/dataset/"
    "6c1af675-1dec-4927-882c-c1ba9d73f76b/resource/"
    "8d9aa2e9-9806-4f26-a4ac-48ba21e9b96d/download/"
    "district_nwic_geojson.zip"
)

output_folder = Path("data/boundaries")
output_folder.mkdir(parents=True, exist_ok=True)

zip_path = output_folder / "india_district_boundaries.zip"

print("Downloading India's district boundaries...")

response = requests.get(url, timeout=120)
response.raise_for_status()

zip_path.write_bytes(response.content)

print("Download completed!")
print("ZIP file size:", round(zip_path.stat().st_size / (1024 * 1024), 2), "MB")

print("\nExtracting files...")

with zipfile.ZipFile(zip_path, "r") as zip_file:
    zip_file.extractall(output_folder)

    print("\nFiles inside the archive:")
    for name in zip_file.namelist():
        print("-", name)

print("\nDistrict boundary files extracted successfully!")
print("Location:", output_folder.resolve())
