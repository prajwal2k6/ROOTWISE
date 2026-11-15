
from pathlib import Path
import geopandas as gpd
import pandas as pd

folder = Path("data/grids/india")
files = sorted(folder.glob("*.parquet"))

print("========== INDIA GRID VERIFICATION ==========")
print("State/UT files found:", len(files))

total_cells = 0
all_ids = set()
duplicate_ids = 0
invalid_files = []

for file in files:
    try:
        df = pd.read_parquet(file)

        count = len(df)
        total_cells += count

        if "grid_id" in df.columns:
            ids = df["grid_id"]
            duplicate_ids += int(ids.duplicated().sum())

        print(f"{file.name}: {count:,} cells")

    except Exception as error:
        invalid_files.append(file.name)
        print("ERROR:", file.name, error)

print("\n========== FINAL SUMMARY ==========")
print("Total Parquet files:", len(files))
print("Total grid cells:", f"{total_cells:,}")
print("Duplicate grid IDs within files:", duplicate_ids)
print("Unreadable files:", len(invalid_files))

print("\nExpected cells: 3,383,254")
print("Count matches:", total_cells == 3383254)

if invalid_files:
    print("Problem files:", invalid_files)

print("\nGrid verification completed!")
