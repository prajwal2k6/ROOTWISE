
import geopandas as gpd
from pathlib import Path

file_path = Path("data/boundaries/district_nwic.GeoJSON")

print("Loading India district boundaries...")

gdf = gpd.read_file(file_path)

print("\n========== DATASET INFORMATION ==========")

print("Total records:", len(gdf))
print("Coordinate Reference System:", gdf.crs)

print("\n========== COLUMN NAMES ==========")
print(gdf.columns.tolist())

print("\n========== FIRST 5 RECORDS ==========")
print(gdf.head())

print("\n========== GEOMETRY INFORMATION ==========")
print("Geometry types:")
print(gdf.geometry.geom_type.value_counts())

print("\n========== GEOMETRY VALIDATION ==========")
print("Valid geometries:", gdf.geometry.is_valid.sum())
print("Invalid geometries:", (~gdf.geometry.is_valid).sum())
print("Empty geometries:", gdf.geometry.is_empty.sum())

print("\n========== GEOGRAPHICAL BOUNDS ==========")
print(gdf.total_bounds)

print("\nBoundary inspection completed!")
