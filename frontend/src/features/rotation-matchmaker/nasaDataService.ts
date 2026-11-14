
import { API_BASE_URL } from "@/services/api";
import { getSession } from "@/services/authService";

export type NasaFarmData = {
  location: {
    latitude: number;
    longitude: number;
  };
  weather: Record<string, { date: string; value: number }[]>;
  soil_moisture: Record<string, { date: string; value: number }[]>;
  satellite_rainfall: Record<string, { date: string; value: number }[]>;
  sources: Record<string, string>;
  warnings: string[];
};

export async function fetchNasaFarmData(
  farmId: number
): Promise<NasaFarmData> {
  const session = await getSession();

  if (!session?.access_token) {
    throw new Error("Please log in to access farm environmental data.");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/nasa-data/farm/${farmId}`,
    {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail || "Unable to load NASA environmental data."
    );
  }

  return result;
}
