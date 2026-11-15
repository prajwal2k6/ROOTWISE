
import geopandas as gpd
from pathlib import Path

input_file = Path("data/boundaries/district_nwic.GeoJSON")
output_folder = Path("data/processed/boundaries")
output_folder.mkdir(parents=True, exist_ok=True)

print("Loading original district boundaries...")
gdf = gpd.read_file(input_file)

print("Original records:", len(gdf))
print("Invalid geometries before repair:", (~gdf.geometry.is_valid).sum())

print("\nRepairing invalid geometries...")
gdf["geometry"] = gdf.geometry.make_valid()

print("Invalid geometries after repair:", (~gdf.geometry.is_valid).sum())
print("Empty geometries:", gdf.geometry.is_empty.sum())

# Keep the India projected CRS for accurate distance and area work
projected_file = output_folder / "india_districts_cleaned.gpkg"
gdf.to_file(projected_file, driver="GPKG")

# Also create a WGS84 copy for web maps and GeoJSON exchange
geojson_file = output_folder / "india_districts_cleaned.geojson"
gdf.to_crs("EPSG:4326").to_file(
    geojson_file,
    driver="GeoJSON"
)

print("\n========== FINAL RESULTS ==========")
print("District records:", len(gdf))
print("Projected CRS:", gdf.crs)
print("Projected file:", projected_file)
print("GeoJSON file:", geojson_file)
print("\nBoundary cleaning completed!")
