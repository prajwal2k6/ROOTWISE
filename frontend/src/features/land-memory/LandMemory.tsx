
"use client";

import { useState } from "react";
import type { SavedFarm } from "@/types/farm";
import { getLandMemoryDetails } from "./landMemoryService";
import "./land-memory.css";

type LandMemoryProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm?: SavedFarm | null;
};

const historicalData: Record<
  string,
  {
    rainfall: number[];
    temperature: number[];
    moisture: number[];
    vegetation: number[];
  }
> = {
  "2022": {
    rainfall: [35, 48, 62, 95, 145, 210, 245, 220, 175, 110, 55, 30],
    temperature: [18, 20, 24, 27, 29, 28, 26, 26, 25, 23, 20, 18],
    moisture: [42, 45, 51, 58, 68, 82, 88, 85, 78, 65, 52, 45],
    vegetation: [35, 39, 45, 52, 68, 79, 86, 88, 81, 70, 52, 40],
  },
  "2023": {
    rainfall: [28, 40, 55, 82, 130, 185, 225, 205, 160, 95, 48, 25],
    temperature: [19, 21, 25, 28, 30, 29, 27, 27, 26, 24, 21, 19],
    moisture: [38, 42, 48, 54, 63, 75, 82, 79, 71, 58, 47, 40],
    vegetation: [32, 36, 43, 49, 61, 74, 82, 84, 76, 64, 48, 36],
  },
  "2024": {
    rainfall: [42, 52, 70, 105, 160, 230, 260, 240, 190, 125, 65, 38],
    temperature: [17, 19, 23, 26, 28, 27, 25, 25, 24, 22, 19, 17],
    moisture: [46, 50, 57, 65, 74, 88, 92, 89, 83, 70, 57, 49],
    vegetation: [38, 42, 50, 60, 72, 84, 91, 90, 85, 73, 57, 44],
  },
  "2025": {
    rainfall: [32, 44, 58, 90, 138, 195, 235, 215, 168, 100, 50, 28],
    temperature: [19, 21, 24, 28, 30, 29, 27, 26, 26, 23, 21, 18],
    moisture: [40, 44, 50, 57, 66, 78, 85, 81, 74, 61, 49, 42],
    vegetation: [33, 37, 45, 53, 65, 77, 85, 86, 78, 67, 50, 38],
  },
};

const months = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function getLinePoints(values: number[], max: number) {
  return values
    .map((value, index) => {
      const x = 10 + index * (280 / 11);
      const y = 105 - (value / max) * 90;
      return `${x},${y}`;
    })
    .join(" ");
}

function getAverage(values: number[]) {
  return Math.round(
    values.reduce((total, value) => total + value, 0) / values.length
  );
}

export default function LandMemory({
  isOpen,
  onClose,
  selectedFarm,
}: LandMemoryProps) {
  const [selectedYear, setSelectedYear] = useState("2025");

  if (!isOpen) return null;

  const feature = getLandMemoryDetails();
  const data = historicalData[selectedYear];

  const farmName =
    selectedFarm && "name" in selectedFarm
      ? String(selectedFarm.name || "Selected farm")
      : "Farm profile not selected";

  const averageRainfall = getAverage(data.rainfall);
  const averageTemperature = getAverage(data.temperature);
  const averageMoisture = getAverage(data.moisture);
  const averageVegetation = getAverage(data.vegetation);

  return (
    <div
      className="lm-page-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="lm-page" role="dialog" aria-modal="true">
        <header className="lm-header">
          <div>
            <div className="lm-eyebrow">ROOTWISE / FEATURE 04</div>
            <h1>Land Memory</h1>
            <p>
              {feature.detail}
            </p>
          </div>

          <button
            className="lm-close"
            onClick={onClose}
            aria-label="Close Land Memory"
          >
            ×
          </button>
        </header>

        <div className="lm-content">
          <section className="lm-hero-card">
            <div>
              <span className="lm-section-label">YOUR LAND, OVER TIME</span>
              <h2>Every field has a story.</h2>
              <p>
                Explore how rainfall, temperature, soil moisture and
                vegetation patterns change through the seasons.
                Understand the environmental history around your farm
                before planning what comes next.
              </p>
            </div>
            <div className="lm-hero-number">04</div>
          </section>

          <section className="lm-farm-strip">
            <div>
              <span className="lm-muted-label">SELECTED FARM</span>
              <strong>{farmName}</strong>
            </div>
            <div>
              <span className="lm-muted-label">DATA PERIOD</span>
              <strong>2022 – 2025</strong>
            </div>
            <div>
              <span className="lm-muted-label">REPORT TYPE</span>
              <strong className="lm-demo-label">Illustrative preview</strong>
            </div>
          </section>

          <section className="lm-section">
            <div className="lm-section-heading">
              <div>
                <span className="lm-section-label">01 / EXPLORE HISTORY</span>
                <h2>Choose a year</h2>
                <p>
                  Switch between years to explore changing environmental
                  patterns in this sample dataset.
                </p>
              </div>
            </div>

            <div className="lm-year-selector">
              {Object.keys(historicalData).map((year) => (
                <button
                  key={year}
                  className={`lm-year-button ${
                    selectedYear === year ? "active" : ""
                  }`}
                  onClick={() => setSelectedYear(year)}
                >
                  {year}
                </button>
              ))}
            </div>

            <div className="lm-demo-notice">
              <span>ⓘ</span>
              <p>
                Demo data only: these values are illustrative and are
                not actual measurements for the selected farm. Historical
                NASA POWER and other environmental data will be connected
                in the next integration stage.
              </p>
            </div>
          </section>

          <section className="lm-section">
            <div className="lm-section-heading">
              <div>
                <span className="lm-section-label">02 / YEARLY SUMMARY</span>
                <h2>Environmental snapshot</h2>
                <p>
                  Average values across the selected year's sample data.
                </p>
              </div>
              <span className="lm-year-tag">{selectedYear}</span>
            </div>

            <div className="lm-stats-grid">
              <div className="lm-stat-card">
                <span className="lm-stat-icon">☂</span>
                <span className="lm-stat-value">{averageRainfall} mm</span>
                <span className="lm-stat-title">Average monthly rainfall</span>
                <span className="lm-stat-note">Rainfall pattern</span>
              </div>

              <div className="lm-stat-card">
                <span className="lm-stat-icon">☀</span>
                <span className="lm-stat-value">{averageTemperature}°C</span>
                <span className="lm-stat-title">Average temperature</span>
                <span className="lm-stat-note">Temperature pattern</span>
              </div>

              <div className="lm-stat-card">
                <span className="lm-stat-icon">◉</span>
                <span className="lm-stat-value">{averageMoisture}%</span>
                <span className="lm-stat-title">Average soil moisture</span>
                <span className="lm-stat-note">Illustrative indicator</span>
              </div>

              <div className="lm-stat-card">
                <span className="lm-stat-icon">✿</span>
                <span className="lm-stat-value">{averageVegetation}%</span>
                <span className="lm-stat-title">Vegetation index</span>
                <span className="lm-stat-note">Illustrative indicator</span>
              </div>
            </div>
          </section>

          <section className="lm-section">
            <div className="lm-section-heading">
              <div>
                <span className="lm-section-label">03 / CLIMATE HISTORY</span>
                <h2>Rainfall through the year</h2>
                <p>
                  Monthly rainfall distribution for {selectedYear}.
                </p>
              </div>
              <span className="lm-chart-unit">Millimetres (mm)</span>
            </div>

            <div className="lm-chart-card">
              <div className="lm-chart-top">
                <strong>Monthly rainfall</strong>
                <span>{selectedYear}</span>
              </div>

              <div className="lm-bar-chart">
                {data.rainfall.map((value, index) => (
                  <div className="lm-bar-column" key={months[index]}>
                    <span className="lm-bar-value">{value}</span>
                    <div className="lm-bar-track">
                      <div
                        className="lm-bar rainfall"
                        style={{ height: `${(value / 280) * 100}%` }}
                      />
                    </div>
                    <span className="lm-month">{months[index]}</span>
                  </div>
                ))}
              </div>
              <div className="lm-chart-footnote">
                Higher bars indicate greater monthly rainfall.
              </div>
            </div>
          </section>

          <section className="lm-section">
            <div className="lm-section-heading">
              <div>
                <span className="lm-section-label">04 / TEMPERATURE HISTORY</span>
                <h2>Temperature patterns</h2>
                <p>
                  Explore how average temperature changes across the months.
                </p>
              </div>
              <span className="lm-chart-unit">Degrees Celsius (°C)</span>
            </div>

            <div className="lm-chart-card">
              <div className="lm-chart-top">
                <strong>Monthly average temperature</strong>
                <span>{selectedYear}</span>
              </div>

              <div className="lm-line-chart">
                <div className="lm-y-labels">
                  <span>35°</span>
                  <span>25°</span>
                  <span>15°</span>
                </div>
                <svg viewBox="0 0 300 120" preserveAspectRatio="none">
                  <line x1="10" y1="15" x2="290" y2="15" className="lm-grid-line" />
                  <line x1="10" y1="60" x2="290" y2="60" className="lm-grid-line" />
                  <line x1="10" y1="105" x2="290" y2="105" className="lm-grid-line" />
                  <polyline
                    points={getLinePoints(data.temperature, 35)}
                    className="lm-temp-line"
                  />
                  {data.temperature.map((value, index) => {
                    const x = 10 + index * (280 / 11);
                    const y = 105 - (value / 35) * 90;
                    return (
                      <circle
                        key={months[index]}
                        cx={x}
                        cy={y}
                        r="3"
                        className="lm-temp-point"
                      />
                    );
                  })}
                </svg>
              </div>
              <div className="lm-month-labels">
                {months.map((month) => <span key={month}>{month}</span>)}
              </div>
            </div>
          </section>

          <section className="lm-section">
            <div className="lm-section-heading">
              <div>
                <span className="lm-section-label">05 / LAND CONDITIONS</span>
                <h2>Soil moisture & vegetation</h2>
                <p>
                  Sample indicators that help describe changes in land
                  conditions across the year.
                </p>
              </div>
            </div>

            <div className="lm-two-charts">
              <div className="lm-chart-card">
                <div className="lm-chart-top">
                  <strong>Soil moisture</strong>
                  <span>%</span>
                </div>
                <div className="lm-small-bars">
                  {data.moisture.map((value, index) => (
                    <div className="lm-small-column" key={months[index]}>
                      <div className="lm-small-track">
                        <div
                          className="lm-bar moisture"
                          style={{ height: `${value}%` }}
                        />
                      </div>
                      <span>{months[index][0]}</span>
                    </div>
                  ))}
                </div>
                <p className="lm-chart-description">
                  Illustrative moisture indicator. Actual soil moisture
                  requires an appropriate observation or dataset.
                </p>
              </div>

              <div className="lm-chart-card">
                <div className="lm-chart-top">
                  <strong>Vegetation index</strong>
                  <span>Index</span>
                </div>
                <div className="lm-small-bars">
                  {data.vegetation.map((value, index) => (
                    <div className="lm-small-column" key={months[index]}>
                      <div className="lm-small-track">
                        <div
                          className="lm-bar vegetation"
                          style={{ height: `${value}%` }}
                        />
                      </div>
                      <span>{months[index][0]}</span>
                    </div>
                  ))}
                </div>
                <p className="lm-chart-description">
                  Illustrative vegetation indicator. A real vegetation
                  index needs satellite observations such as NDVI.
                </p>
              </div>
            </div>
          </section>

          <section className="lm-section">
            <div className="lm-section-heading">
              <div>
                <span className="lm-section-label">06 / SEASONAL TIMELINE</span>
                <h2>How the year unfolds</h2>
                <p>
                  A simplified view of the sample environmental cycle.
                </p>
              </div>
            </div>

            <div className="lm-timeline">
              <div className="lm-timeline-item">
                <span className="lm-timeline-dot spring" />
                <span className="lm-timeline-month">JAN – MAR</span>
                <h3>Early season</h3>
                <p>
                  Sample rainfall is relatively lower. Monitor water
                  availability and prepare for the upcoming growing season.
                </p>
              </div>
              <div className="lm-timeline-item">
                <span className="lm-timeline-dot summer" />
                <span className="lm-timeline-month">APR – JUN</span>
                <h3>Season transition</h3>
                <p>
                  Rainfall begins to increase in this sample pattern.
                  Temperature and moisture conditions may change.
                </p>
              </div>
              <div className="lm-timeline-item">
                <span className="lm-timeline-dot monsoon" />
                <span className="lm-timeline-month">JUL – SEP</span>
                <h3>Rainy period</h3>
                <p>
                  Higher rainfall and moisture values appear in the
                  illustrative dataset. Consider drainage and waterlogging
                  risks where relevant.
                </p>
              </div>
              <div className="lm-timeline-item">
                <span className="lm-timeline-dot winter" />
                <span className="lm-timeline-month">OCT – DEC</span>
                <h3>Late season</h3>
                <p>
                  Sample rainfall declines. Review remaining moisture
                  and plan the next crop cycle.
                </p>
              </div>
            </div>
          </section>

          <section className="lm-section">
            <div className="lm-section-heading">
              <div>
                <span className="lm-section-label">07 / KEY OBSERVATIONS</span>
                <h2>What can we learn?</h2>
                <p>
                  Example interpretations based on the illustrative
                  patterns shown above.
                </p>
              </div>
            </div>

            <div className="lm-observations">
              <div>
                <span className="lm-observation-icon">☂</span>
                <div>
                  <h3>Rainfall is seasonally concentrated</h3>
                  <p>
                    The sample pattern shows greater rainfall during the
                    middle of the year. Seasonal water planning may be useful.
                  </p>
                </div>
              </div>
              <div>
                <span className="lm-observation-icon">☀</span>
                <div>
                  <h3>Temperature changes across seasons</h3>
                  <p>
                    Temperature patterns can help provide context when
                    comparing crop growing periods and seasonal conditions.
                  </p>
                </div>
              </div>
              <div>
                <span className="lm-observation-icon">✿</span>
                <div>
                  <h3>Vegetation patterns vary over time</h3>
                  <p>
                    Satellite-derived vegetation indices can help monitor
                    changes in vegetation activity, but do not identify
                    every cause of that change.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="lm-bottom-card">
            <span className="lm-section-label">ROOTWISE / LAND MEMORY</span>
            <h2>Understand the past. Plan the next season.</h2>
            <p>
              Historical environmental patterns can provide valuable
              context for agricultural decisions. They work best when
              combined with local field observations and farmer knowledge.
            </p>
            <button className="lm-back-button" onClick={onClose}>
              ← Back to ROOTWISE
            </button>
          </section>

          <footer className="lm-footer">
            ROOTWISE · Your land, remembered over time
          </footer>
        </div>
      </div>
    </div>
  );
}
