import geopandas as gpd
from pathlib import Path

file = Path("data/grids/india/Karnataka_1km_grid.parquet")

gdf = gpd.read_parquet(file)

print("========== GRID GEOMETRY CHECK ==========")

print("Total cells:", len(gdf))
print("CRS:", gdf.crs)
print("Geometry types:")
print(gdf.geom_type.value_counts())

print("Invalid geometries:", (~gdf.geometry.is_valid).sum())
print("Empty geometries:", gdf.geometry.is_empty.sum())

print("Total area (km2):", round(gdf.area.sum() / 1_000_000, 2))

print("\nSample records:")
print(gdf.head())

print("\nGeometry check completed!")