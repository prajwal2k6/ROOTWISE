import { FarmMapData } from "@/components/FarmMap";

export type { FarmMapData };

export type SavedFarm = {
  id: number;
  farm_name: string;
  latitude: number;
  longitude: number;
  boundary: [number, number][];
  area_acres: number;
  area_hectares: number;
  soil_type?: string | null;
  irrigation?: string | null;
  main_crop?: string | null;
  other_crops?: string | null;
  sowing_season?: string | null;
  harvest_period?: string | null;
  previous_crop_sequence?: string | null;
  crop_frequency?: string | null;
  priority?: string | null;
  notes?: string | null;
};

export type FarmData = {
  farmName: string;
  acres: string;
  soil: string;
  irrigation: string;
  mainCrop: string;
  otherCrops: string;
  sowing: string;
  harvest: string;
  sequence: string;
  frequency: string;
  priority: string;
  notes: string;
  location: string;
  locationMethod: string;
};

export const emptyFarm: FarmData = {
  farmName: "Green Valley Farm",
  acres: "5",
  soil: "Red loamy soil",
  irrigation: "Borewell",
  mainCrop: "Ragi (finger millet)",
  otherCrops: "Maize, tomato, groundnut",
  sowing: "Kharif (June–July)",
  harvest: "October–December",
  sequence: "Ragi → Groundnut → Maize",
  frequency: "Twice a year",
  priority: "Save water and manage dry periods",
  notes: "Water availability is lower during March and April.",
  location: "",
  locationMethod: "",
};
