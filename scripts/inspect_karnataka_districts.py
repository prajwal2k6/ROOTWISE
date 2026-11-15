
import geopandas as gpd

file = "data/grids/india/Karnataka_1km_grid.parquet"

gdf = gpd.read_parquet(file)

print("Total Karnataka grid cells:", len(gdf))

print("\nDistrict names:")
print(sorted(gdf["district"].dropna().unique()))

print("\nGrid cells per district:")
print(gdf.groupby("district").size().sort_values(ascending=False))
