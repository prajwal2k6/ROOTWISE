
"use client";

import { useEffect, useState } from "react";
import {
  fetchNasaFarmData,
  type NasaFarmData,
} from "./nasaDataService";

type Props = {
  farmId: number;
};

function latestValue(
  data: Record<string, { date: string; value: number }[]>,
  key: string
) {
  const values = data[key];

  if (!values?.length) return null;

  return values[values.length - 1];
}

function formatValue(value: number | null, unit: string) {
  if (value === null || !Number.isFinite(value)) return "Unavailable";
  return `${value.toFixed(2)} ${unit}`;
}

export default function NasaInsights({ farmId }: Props) {
  const [data, setData] = useState<NasaFarmData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadData() {
      try {
        setLoading(true);
        setError("");

        const result = await fetchNasaFarmData(farmId);

        if (active) setData(result);
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load NASA data."
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, [farmId]);

  if (loading) {
    return <div className="rm-nasa-panel">Loading NASA environmental data...</div>;
  }

  if (error || !data) {
    return (
      <div className="rm-nasa-panel">
        <h3>Environmental Data</h3>
        <p>{error || "NASA data is unavailable."}</p>
      </div>
    );
  }

  const temperature = latestValue(data.weather, "T2M");
  const rainfall = latestValue(data.weather, "PRECTOTCORR");
  const humidity = latestValue(data.weather, "RH2M");
  const soilMoisture = latestValue(data.soil_moisture, "SFMC");
  const satelliteRainfall = Object.values(data.satellite_rainfall)
    .flat()
    .at(-1);

  const metrics = [
    {
      label: "Temperature",
      value: formatValue(temperature?.value ?? null, "°C"),
      date: temperature?.date,
    },
    {
      label: "Rainfall",
      value: formatValue(rainfall?.value ?? null, "mm/day"),
      date: rainfall?.date,
    },
    {
      label: "Humidity",
      value: formatValue(humidity?.value ?? null, "%"),
      date: humidity?.date,
    },
    {
      label: "Soil moisture",
      value: formatValue(soilMoisture?.value ?? null, "m³/m³"),
      date: soilMoisture?.date,
    },
    {
      label: "Satellite rainfall",
      value: formatValue(satelliteRainfall?.value ?? null, "mm/day"),
      date: satelliteRainfall?.date,
    },
  ];

  return (
    <section className="rm-nasa-panel">
      <div className="rm-section-heading">
        <h2>NASA Environmental Insights</h2>
        <p>
          Environmental observations for your farm location.
          These are satellite and model-derived regional indicators,
          not direct field measurements.
        </p>
      </div>

      <div className="rm-nasa-grid">
        {metrics.map((metric) => (
          <div className="rm-nasa-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            {metric.date && <small>Observation: {metric.date}</small>}
          </div>
        ))}
      </div>

      <div className="rm-nasa-sources">
        <strong>Data source status</strong>
        {Object.entries(data.sources).map(([source, status]) => (
          <span key={source}>
            {source}: {status}
          </span>
        ))}
      </div>

      {data.warnings.length > 0 && (
        <p className="rm-nasa-warning">
          Some datasets could not be retrieved. Missing observations
          will not be treated as zero.
        </p>
      )}
    </section>
  );
}
