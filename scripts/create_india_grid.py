
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from pathlib import Path
import math
import re
import gc

# Input and output locations
input_file = Path("data/processed/boundaries/india_districts_cleaned.gpkg")
output_folder = Path("data/grids/india")
output_folder.mkdir(parents=True, exist_ok=True)

GRID_SIZE = 1000  # 1 km in metres

print("Loading cleaned India district boundaries...")
districts = gpd.read_file(input_file)

if districts.crs is None:
    raise ValueError("Boundary dataset has no CRS.")

districts = districts.to_crs("EPSG:7755")

print("Total district records:", len(districts))
print("Starting state-by-state grid generation...")

def safe_name(name):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(name)).strip("_")

total_cells = 0

for state_name, state_data in districts.groupby("state_name", sort=True):

    print(f"\nProcessing state/UT: {state_name}")
    state_grids = []

    for _, district_row in state_data.iterrows():

        district_name = district_row["district"]
        boundary = district_row.geometry

        if boundary is None or boundary.is_empty:
            print("Skipping empty district:", district_name)
            continue

        minx, miny, maxx, maxy = boundary.bounds

        cells = []
        x = math.floor(minx / GRID_SIZE) * GRID_SIZE

        while x < maxx:
            y = math.floor(miny / GRID_SIZE) * GRID_SIZE

            while y < maxy:
                square = box(
                    x, y,
                    x + GRID_SIZE,
                    y + GRID_SIZE
                )

                clipped = square.intersection(boundary)

                if not clipped.is_empty and clipped.area > 0:
                    cells.append({
                        "state_name": state_name,
                        "district": district_name,
                        "dtcode": str(district_row["dtcode"]),
                        "grid_id": (
                            f'{district_row["stcode"]}_'
                            f'{district_row["dtcode"]}_'
                            f'{x}_{y}'
                        ),
                        "area_m2": clipped.area,
                        "geometry": clipped
                    })

                y += GRID_SIZE

            x += GRID_SIZE

        if cells:
            district_grid = gpd.GeoDataFrame(
                cells,
                geometry="geometry",
                crs="EPSG:7755"
            )
            state_grids.append(district_grid)

        print(
            f"  {district_name}: "
            f"{len(cells):,} cells"
        )

    if state_grids:
        state_grid = gpd.GeoDataFrame(
            pd.concat(state_grids, ignore_index=True),
            geometry="geometry",
            crs="EPSG:7755"
        )

        output_file = (
            output_folder /
            f"{safe_name(state_name)}_1km_grid.parquet"
        )

        state_grid.to_parquet(output_file)

        state_count = len(state_grid)
        total_cells += state_count

        print(f"Saved: {output_file}")
        print(f"State total: {state_count:,} cells")

        del state_grid
        del state_grids
        gc.collect()

print("\n================================")
print("INDIA GRID GENERATION COMPLETED")
print("District records processed:", len(districts))
print("Total grid cells:", f"{total_cells:,}")
print("Output folder:", output_folder)
print("================================")
