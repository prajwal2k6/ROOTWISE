
import xarray as xr
import matplotlib.pyplot as plt

file_path = "data/processed/gpm/gpm_india_20160101.nc"

print("Loading India rainfall data...")

ds = xr.open_dataset(file_path)

rainfall = ds["precipitation"].isel(time=0)

plt.figure(figsize=(10, 8))

rainfall.plot(
    x="lon",
    y="lat",
    cmap="Blues",
    cbar_kwargs={"label": "Rainfall (mm/day)"}
)

plt.title("NASA GPM Daily Rainfall - India Region")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.savefig(
    "data/outputs/gpm_india_20160101.png",
    dpi=200,
    bbox_inches="tight"
)

plt.show()
ds.close()

print("Rainfall map saved successfully!")
