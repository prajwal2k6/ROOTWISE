
import geopandas as gpd

file_path = "data/processed/boundaries/india_districts_cleaned.gpkg"

gdf = gpd.read_file(file_path)

print("========== CLEANED BOUNDARY VERIFICATION ==========")
print("Total districts:", len(gdf))
print("CRS:", gdf.crs)
print("Invalid geometries:", (~gdf.geometry.is_valid).sum())
print("Empty geometries:", gdf.geometry.is_empty.sum())

print("\nSample district names:")
print(gdf[["state_name", "district"]].head(10))

print("\nVerification completed!")
