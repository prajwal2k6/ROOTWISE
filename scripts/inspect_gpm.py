
import xarray as xr
from pathlib import Path

file_path = Path(
    "data/raw/gpm/"
    "3B-DAY.MS.MRG.3IMERG.20160101-S000000-E235959.V07B.nc4"
)

print("Opening NASA GPM rainfall file...")

with xr.open_dataset(file_path, engine="netcdf4") as ds:
    print("\n========== DATASET INFORMATION ==========")
    print(ds)

    print("\n========== VARIABLES ==========")
    for name in ds.data_vars:
        print("\nVariable:", name)
        print("Dimensions:", ds[name].dims)
        print("Attributes:", ds[name].attrs)

    print("\n========== COORDINATES ==========")
    print(ds.coords)

print("\nGPM file inspection completed!")
