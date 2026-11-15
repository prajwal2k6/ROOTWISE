
import geopandas as gpd
from shapely.geometry import box
from pathlib import Path
import math

# Load cleaned district boundaries
boundary_file = "data/processed/boundaries/india_districts_cleaned.gpkg"
gdf = gpd.read_file(boundary_file)

# Select one district for testing
district = gdf[
    (gdf["state_name"] == "Madhya Pradesh") &
    (gdf["district"] == "Indore")
]

if district.empty:
    raise ValueError("Indore district not found!")

# Use India's projected CRS (metres)
district = district.to_crs("EPSG:7755")
boundary = district.geometry.union_all()

# Create 1 km x 1 km grid
grid_size = 1000
minx, miny, maxx, maxy = boundary.bounds

print("Creating 1 km grid for Indore...")
print("District: Indore, Madhya Pradesh")
print("Grid cell size:", grid_size, "metres")

cells = []
cell_id = 1

x = math.floor(minx / grid_size) * grid_size

while x < maxx:
    y = math.floor(miny / grid_size) * grid_size

    while y < maxy:
        square = box(x, y, x + grid_size, y + grid_size)

        # Keep only cells that intersect the district
        clipped = square.intersection(boundary)

        if not clipped.is_empty and clipped.area > 0:
            cells.append({
                "grid_id": cell_id,
                "geometry": clipped
            })
            cell_id += 1

        y += grid_size

    x += grid_size

grid = gpd.GeoDataFrame(
    cells,
    geometry="geometry",
    crs="EPSG:7755"
)

# Save the pilot grid
output_folder = Path("data/grids")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "indore_1km_grid.gpkg"
grid.to_file(output_file, driver="GPKG")

print("\n========== GRID RESULTS ==========")
print("Total grid cells:", len(grid))
print("CRS:", grid.crs)
print("Grid size: 1 km x 1 km")
print("Output:", output_file)
print("\nGrid pilot completed!")
