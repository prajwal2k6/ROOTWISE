
import json
from pathlib import Path

full_file = Path("data/outputs/bengaluru_urban_20160101.json")
sample_file = Path("data/outputs/bengaluru_urban_sample_3_cells.json")

with full_file.open("r", encoding="utf-8") as f:
    data = json.load(f)

sample = data.copy()
sample["cells"] = data["cells"][:3]

with sample_file.open("w", encoding="utf-8") as f:
    json.dump(sample, f, indent=2, allow_nan=False)

print("Sample created successfully!")
print("Sample cells:", len(sample["cells"]))
print("File:", sample_file)
