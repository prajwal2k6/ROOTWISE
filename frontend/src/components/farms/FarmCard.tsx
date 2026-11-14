"use client";

import type { SavedFarm } from "@/types/farm";

type FarmCardProps = {
  farm: SavedFarm;
  isSelected: boolean;
  onSelect: () => void;
};

export default function FarmCard({ farm, isSelected, onSelect }: FarmCardProps) {
  return (
    <button
      type="button"
      className={`rw-saved-farm ${isSelected ? "selected" : ""}`}
      onClick={onSelect}
    >
      <span className="rw-farm-card-top">
        <strong>{farm.farm_name}</strong>
        {isSelected && <span className="rw-selected-label">SELECTED</span>}
      </span>
      <span>
        {farm.area_acres.toFixed(2)} acres · {farm.main_crop || "Crop not specified"}
      </span>
      <span>
        {farm.soil_type || "Soil not specified"} · {farm.irrigation || "Irrigation not specified"}
      </span>
      <span className="rw-farm-coordinates">
        {farm.latitude.toFixed(5)}, {farm.longitude.toFixed(5)}
      </span>
    </button>
  );
}
