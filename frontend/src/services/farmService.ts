import { API_BASE_URL } from "./api";
import type { SavedFarm, FarmData, FarmMapData } from "@/types/farm";

export type CreateFarmPayload = {
  farm_name: string;
  latitude: number;
  longitude: number;
  boundary: [number, number][];
  area_acres: number;
  area_hectares: number;
  soil_type?: string;
  irrigation?: string;
  main_crop?: string;
  other_crops?: string;
  sowing_season?: string;
  harvest_period?: string;
  previous_crop_sequence?: string;
  crop_frequency?: string;
  priority?: string;
  notes?: string;
};

export async function fetchMyFarms(accessToken: string): Promise<SavedFarm[]> {
  const response = await fetch(`${API_BASE_URL}/api/farms/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error(`Could not load farms (${response.status}).`);
  }
  return await response.json();
}

export async function createFarm(
  payload: CreateFarmPayload,
  accessToken: string
): Promise<SavedFarm> {
  const response = await fetch(`${API_BASE_URL}/api/farms/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.detail || `Farm save failed (${response.status}).`);
  }
  return result;
}

export function buildFarmPayload(
  farm: FarmData,
  mapData: FarmMapData
): CreateFarmPayload {
  return {
    farm_name: farm.farmName.trim(),
    latitude: mapData.latitude,
    longitude: mapData.longitude,
    boundary: mapData.boundary,
    area_acres: Number(farm.acres || mapData.areaAcres),
    area_hectares: mapData.areaHectares,
    soil_type: farm.soil,
    irrigation: farm.irrigation,
    main_crop: farm.mainCrop,
    other_crops: farm.otherCrops,
    sowing_season: farm.sowing,
    harvest_period: farm.harvest,
    previous_crop_sequence: farm.sequence,
    crop_frequency: farm.frequency,
    priority: farm.priority,
    notes: farm.notes,
  };
}
