
import xarray as xr
from pathlib import Path

input_file = Path(
    "data/raw/gpm/"
    "3B-DAY.MS.MRG.3IMERG.20160101-S000000-E235959.V07B.nc4"
)

output_folder = Path("data/processed/gpm")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "gpm_india_20160101.nc"

print("Opening global GPM dataset...")

with xr.open_dataset(input_file, engine="netcdf4") as ds:

    print("Extracting India region...")

    india = ds.sel(
        lon=slice(68, 98),
        lat=slice(6, 37.5)
    )

    rainfall = india["precipitation"]

    print("\n========== INDIA RAINFALL SUMMARY ==========")
    print("Date:", str(india.time.values[0]))
    print("Grid dimensions:", india.sizes)
    print("Resolution: 0.1 degree")
    print("Rainfall units:", rainfall.attrs["units"])
    print("Minimum:", float(rainfall.min().values), "mm/day")
    print("Maximum:", float(rainfall.max().values), "mm/day")
    print("Mean:", float(rainfall.mean().values), "mm/day")

    print("\nSaving India subset...")

    india.to_netcdf(output_file)

print("\nIndia GPM extraction completed!")
print("Saved:", output_file)
