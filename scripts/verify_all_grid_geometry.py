
from pathlib import Path
import geopandas as gpd

folder = Path("data/grids/india")
files = sorted(folder.glob("*.parquet"))

expected_crs = "EPSG:7755"

total_cells = 0
total_invalid = 0
total_empty = 0
wrong_crs = []
unreadable = []

print("========== INDIA GRID GEOMETRY VALIDATION ==========")
print("Files found:", len(files))

for file in files:
    try:
        gdf = gpd.read_parquet(file)

        cells = len(gdf)
        invalid = int((~gdf.geometry.is_valid).sum())
        empty = int(gdf.geometry.is_empty.sum())

        crs = gdf.crs
        crs_ok = crs is not None and crs.to_epsg() == 7755

        total_cells += cells
        total_invalid += invalid
        total_empty += empty

        if not crs_ok:
            wrong_crs.append(file.name)

        print(
            f"{file.name}: "
            f"Cells={cells:,}, "
            f"Invalid={invalid}, "
            f"Empty={empty}, "
            f"CRS={'OK' if crs_ok else 'WRONG'}"
        )

    except Exception as error:
        unreadable.append(file.name)
        print("ERROR:", file.name, error)

print("\n========== FINAL SUMMARY ==========")
print("Total files:", len(files))
print("Total grid cells:", f"{total_cells:,}")
print("Invalid geometries:", total_invalid)
print("Empty geometries:", total_empty)
print("Wrong CRS files:", len(wrong_crs))
print("Unreadable files:", len(unreadable))

print("\n========== RESULT ==========")

if (
    len(files) == 36
    and total_cells == 3383254
    and total_invalid == 0
    and total_empty == 0
    and not wrong_crs
    and not unreadable
):
    print("ALL GEOMETRY CHECKS PASSED!")
else:
    print("SOME CHECKS NEED ATTENTION.")

print("\nVerification completed!")
