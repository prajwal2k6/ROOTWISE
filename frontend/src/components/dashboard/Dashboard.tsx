
"use client";

import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  AreaChart,
  Area,
  Line,
  Legend,
} from "recharts";

import "./dashboard.css";

const cropData = [
  { crop: "Rice", yield: 4.2, water: 88 },
  { crop: "Maize", yield: 5.1, water: 62 },
  { crop: "Ragi", yield: 3.4, water: 35 },
  { crop: "Groundnut", yield: 2.8, water: 48 },
  { crop: "Pulses", yield: 2.2, water: 30 },
];

const strategies = [
  { id: "existing", name: "Existing rotation", color: "#9da995" },
  { id: "restoration", name: "Soil restoration", color: "#91bd55" },
  { id: "climate", name: "Climate resilience", color: "#4e856b" },
];

const strategyData = [
  { factor: "Climate fit", existing: 65, restoration: 78, climate: 92 },
  { factor: "Water efficiency", existing: 48, restoration: 75, climate: 90 },
  { factor: "Soil benefits", existing: 52, restoration: 94, climate: 76 },
  { factor: "Season fit", existing: 72, restoration: 80, climate: 88 },
  { factor: "Risk management", existing: 50, restoration: 82, climate: 91 },
];

const months = [
  { month: "Jan", moisture: 3, heat: 1, rainfall: 2 },
  { month: "Feb", moisture: 3, heat: 2, rainfall: 2 },
  { month: "Mar", moisture: 2, heat: 3, rainfall: 1 },
  { month: "Apr", moisture: 1, heat: 3, rainfall: 1 },
  { month: "May", moisture: 2, heat: 3, rainfall: 2 },
  { month: "Jun", moisture: 3, heat: 2, rainfall: 3 },
  { month: "Jul", moisture: 3, heat: 1, rainfall: 3 },
  { month: "Aug", moisture: 3, heat: 1, rainfall: 3 },
  { month: "Sep", moisture: 2, heat: 2, rainfall: 3 },
  { month: "Oct", moisture: 3, heat: 2, rainfall: 3 },
  { month: "Nov", moisture: 3, heat: 1, rainfall: 2 },
  { month: "Dec", moisture: 3, heat: 1, rainfall: 2 },
];

const yieldData = [
  { month: "Jan", lower: 2.1, range: 0.8, median: 2.5 },
  { month: "Feb", lower: 2.2, range: 0.9, median: 2.7 },
  { month: "Mar", lower: 2.3, range: 1.0, median: 2.9 },
  { month: "Apr", lower: 2.0, range: 1.1, median: 2.6 },
  { month: "May", lower: 2.2, range: 0.9, median: 2.8 },
  { month: "Jun", lower: 2.5, range: 0.8, median: 3.0 },
  { month: "Jul", lower: 2.7, range: 0.9, median: 3.2 },
  { month: "Aug", lower: 2.8, range: 0.8, median: 3.3 },
];

const evidenceItems = [
  {
    title: "Environmental observations",
    detail: "Historical rainfall and temperature patterns are represented using prototype sample values.",
  },
  {
    title: "Crop information",
    detail: "Crop water requirements and seasonal suitability are illustrative comparison factors.",
  },
  {
    title: "Potential benefits",
    detail: "Crop diversity may support soil protection, nutrient cycling and risk management.",
  },
  {
    title: "Missing information",
    detail: "Recent soil tests, field-level moisture readings and verified farm measurements are not yet connected.",
  },
];

function getHeatColor(value: number, type: string) {
  if (type === "heat") {
    return ["", "#dcebd0", "#f1d99b", "#d98c6b"][value];
  }

  if (type === "rainfall") {
    return ["", "#f2dfbd", "#c4dcb9", "#7da987"][value];
  }

  return ["", "#e6c7a9", "#e6e9bd", "#9cbd83"][value];
}

export default function Dashboard() {
  const [selectedStrategies, setSelectedStrategies] = useState([
    "existing",
    "restoration",
    "climate",
  ]);

  const [temperature, setTemperature] = useState(0);
  const [rainfall, setRainfall] = useState(0);
  const [scenario, setScenario] = useState("normal");
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  const rankings = useMemo(() => {
    return [
      {
        name: "Climate resilience",
        score: Math.max(40, 91 - temperature * 2 + rainfall * 0.15),
      },
      {
        name: "Soil restoration",
        score: Math.max(40, 84 - temperature + rainfall * 0.1),
      },
      {
        name: "Existing rotation",
        score: Math.max(35, 70 - temperature * 1.5 + rainfall * 0.05),
      },
    ].sort((a, b) => b.score - a.score);
  }, [temperature, rainfall]);

  function applyPreset(type: string) {
    setScenario(type);

    if (type === "dry") {
      setTemperature(1);
      setRainfall(-20);
    } else if (type === "hot") {
      setTemperature(3);
      setRainfall(0);
    } else {
      setTemperature(0);
      setRainfall(0);
    }
  }

  function toggleStrategy(id: string) {
    setSelectedStrategies((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  }

  return (
    <section className="rd-dashboard">
      <div className="rd-container">

        {/* HEADER */}
        <div className="rd-topline">
          <span>ROOTWISE / FARM INTELLIGENCE</span>
          <span className="rd-live-label">
            <span className="rd-status-dot" />
            PROTOTYPE DATA
          </span>
        </div>

        <header className="rd-header">
          <div>
            <p className="rd-eyebrow">YOUR LAND · YOUR FUTURE</p>
            <h1>Farmer <span>Dashboard.</span></h1>
            <p className="rd-description">
              Understand your land, explore crop rotation possibilities
              and prepare for changing environmental conditions.
            </p>
          </div>

          <div className="rd-date">
            <span>DASHBOARD OVERVIEW</span>
            <strong>ROOTWISE M4</strong>
          </div>
        </header>

        {/* DISCLAIMER */}
        <div className="rd-disclaimer">
          <span>ⓘ</span>
          <p>
            <strong>Prototype information:</strong> The charts and scores
            currently use illustrative sample data. They are not live NASA
            observations, agricultural forecasts or guaranteed yield estimates.
            Always review recommendations with local agricultural experts.
          </p>
        </div>

        {/* OVERVIEW METRICS */}
        <section className="rd-section">
          <div className="rd-section-heading">
            <div>
              <p className="rd-eyebrow">AT A GLANCE</p>
              <h2>Your farm overview</h2>
            </div>
            <span className="rd-muted">Illustrative indicators</span>
          </div>

          <div className="rd-metric-grid">
            <article className="rd-metric-card">
              <div className="rd-metric-top">
                <span className="rd-metric-icon">🌱</span>
                <span className="rd-sample-tag">SAMPLE</span>
              </div>
              <p>Crop performance</p>
              <strong>4.2 t/ha</strong>
              <span className="rd-metric-status">Illustrative crop yield</span>
            </article>

            <article className="rd-metric-card">
              <div className="rd-metric-top">
                <span className="rd-metric-icon">💧</span>
                <span className="rd-sample-tag">SAMPLE</span>
              </div>
              <p>Water efficiency</p>
              <strong>76 / 100</strong>
              <span className="rd-metric-status">Illustrative comparison score</span>
            </article>

            <article className="rd-metric-card">
              <div className="rd-metric-top">
                <span className="rd-metric-icon">🌍</span>
                <span className="rd-sample-tag">SAMPLE</span>
              </div>
              <p>Rotation confidence</p>
              <strong>82%</strong>
              <span className="rd-metric-status">Prototype confidence indicator</span>
            </article>
          </div>
        </section>

        {/* MODULE 1 */}
        <section className="rd-section rd-chart-section">
          <div className="rd-section-heading">
            <div>
              <p className="rd-eyebrow">01 / CROP ANALYSIS</p>
              <h2>Crop Performance</h2>
              <p className="rd-section-description">
                Compare illustrative crop yields across different crop types.
              </p>
            </div>
            <span className="rd-module-tag">BAR CHART</span>
          </div>

          <div className="rd-chart-card">
            <div className="rd-chart-heading">
              <strong>Estimated yield comparison</strong>
              <span>Tonnes per hectare · Sample data</span>
            </div>

            <div className="rd-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cropData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ecdf" />
                  <XAxis dataKey="crop" tick={{ fill: "#788675", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#788675", fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="yield" name="Yield (t/ha)" fill="#91bd55" radius={[7, 7, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* MODULE 2 */}
        <section className="rd-section rd-chart-section">
          <div className="rd-section-heading">
            <div>
              <p className="rd-eyebrow">02 / ROTATION COMPARISON</p>
              <h2>Rotation Strategies</h2>
              <p className="rd-section-description">
                Compare how different rotation approaches perform across
                five decision factors.
              </p>
            </div>
            <span className="rd-module-tag">RADAR CHART</span>
          </div>

          <div className="rd-chart-card">
            <div className="rd-chart-heading">
              <strong>Strategy comparison</strong>
              <span>Select strategies to show or hide them</span>
            </div>

            <div className="rd-strategy-toggles">
              {strategies.map((strategy) => (
                <button
                  type="button"
                  key={strategy.id}
                  className={`rd-strategy-toggle ${
                    selectedStrategies.includes(strategy.id) ? "active" : ""
                  }`}
                  onClick={() => toggleStrategy(strategy.id)}
                  aria-pressed={selectedStrategies.includes(strategy.id)}
                >
                  <span style={{ background: strategy.color }} />
                  {strategy.name}
                </button>
              ))}
            </div>

            <div className="rd-chart rd-radar-chart">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={strategyData}>
                  <PolarGrid stroke="#e3e9dc" />
                  <PolarAngleAxis
                    dataKey="factor"
                    tick={{ fill: "#71806d", fontSize: 10 }}
                  />
                  <PolarRadiusAxis
                    domain={[0, 100]}
                    tick={{ fill: "#9aa493", fontSize: 9 }}
                  />
                  <Tooltip />
                  {strategies.map((strategy) =>
                    selectedStrategies.includes(strategy.id) ? (
                      <Radar
                        key={strategy.id}
                        name={strategy.name}
                        dataKey={strategy.id}
                        stroke={strategy.color}
                        fill={strategy.color}
                        fillOpacity={0.13}
                      />
                    ) : null
                  )}
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* MODULE 3 */}
        <section className="rd-section rd-chart-section">
          <div className="rd-section-heading">
            <div>
              <p className="rd-eyebrow">03 / SEASONAL CONDITIONS</p>
              <h2>Soil Health Calendar</h2>
              <p className="rd-section-description">
                Explore sample monthly indicators for soil moisture,
                heat stress and rainfall.
              </p>
            </div>
            <span className="rd-module-tag">HEATMAP</span>
          </div>

          <div className="rd-chart-card">
            <div className="rd-chart-heading">
              <strong>Monthly stress indicators</strong>
              <span>Illustrative seasonal pattern</span>
            </div>

            <div className="rd-heatmap-wrap">
              <table className="rd-heatmap">
                <thead>
                  <tr>
                    <th>Indicator</th>
                    {months.map((item) => (
                      <th key={item.month}>{item.month}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { key: "moisture", label: "Soil moisture", type: "moisture" },
                    { key: "heat", label: "Heat stress", type: "heat" },
                    { key: "rainfall", label: "Rainfall", type: "rainfall" },
                  ].map((row) => (
                    <tr key={row.key}>
                      <th>{row.label}</th>
                      {months.map((item) => {
                        const value = item[row.key as keyof typeof item] as number;
                        return (
                          <td key={item.month}>
                            <span
                              className="rd-heat-cell"
                              style={{ background: getHeatColor(value, row.type) }}
                              title={`${row.label}: ${value === 1 ? "Low" : value === 2 ? "Moderate" : "High"}`}
                            >
                              {value === 1 ? "L" : value === 2 ? "M" : "H"}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="rd-heat-legend">
              <span><i style={{ background: "#e6c7a9" }} /> Low</span>
              <span><i style={{ background: "#e6e9bd" }} /> Moderate</span>
              <span><i style={{ background: "#9cbd83" }} /> High</span>
            </div>

            <p className="rd-heat-note">
              L = Low · M = Moderate · H = High. The meaning of high
              or low depends on the indicator being measured.
            </p>
          </div>
        </section>

        {/* MODULE 4 */}
        <section className="rd-section rd-chart-section">
          <div className="rd-section-heading">
            <div>
              <p className="rd-eyebrow">04 / UNCERTAINTY ANALYSIS</p>
              <h2>Yield Confidence</h2>
              <p className="rd-section-description">
                View an illustrative yield range rather than relying
                on a single fixed estimate.
              </p>
            </div>
            <span className="rd-module-tag">AREA CHART</span>
          </div>

          <div className="rd-chart-card">
            <div className="rd-confidence-summary">
              <div>
                <span className="rd-muted">PROTOTYPE CONFIDENCE</span>
                <strong>82%</strong>
              </div>
              <span className="rd-confidence-label">Illustrative · Medium-high</span>
            </div>

            <div className="rd-chart">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={yieldData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ecdf" />
                  <XAxis dataKey="month" tick={{ fill: "#788675", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#788675", fontSize: 11 }} />
                  <Tooltip />
                  <Area
                    dataKey="lower"
                    stackId="confidence"
                    stroke="none"
                    fill="transparent"
                    name="Lower range"
                  />
                  <Area
                    dataKey="range"
                    stackId="confidence"
                    stroke="none"
                    fill="#b9d59a"
                    fillOpacity={0.5}
                    name="Confidence range"
                  />
                  <Line
                    type="monotone"
                    dataKey="median"
                    stroke="#527d43"
                    strokeWidth={3}
                    dot={{ fill: "#527d43", r: 3 }}
                    name="Median estimate"
                  />
                  <Legend />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <p className="rd-heat-note">
              The shaded region represents an illustrative range,
              not a statistically validated prediction interval.
            </p>
          </div>
        </section>

        {/* WHAT-IF SIMULATOR */}
        <section className="rd-section rd-simulator">
          <div className="rd-section-heading">
            <div>
              <p className="rd-eyebrow">EXPLORE POSSIBLE CONDITIONS</p>
              <h2>What-if Simulator</h2>
              <p className="rd-section-description">
                Change temperature and rainfall assumptions to see
                how the sample strategy rankings respond.
              </p>
            </div>
            <span className="rd-module-tag">INTERACTIVE</span>
          </div>

          <div className="rd-chart-card">
            <div className="rd-presets">
              <button
                type="button"
                className={scenario === "normal" ? "selected" : ""}
                onClick={() => applyPreset("normal")}
              >
                Normal conditions
              </button>
              <button
                type="button"
                className={scenario === "dry" ? "selected" : ""}
                onClick={() => applyPreset("dry")}
              >
                Dry year
              </button>
              <button
                type="button"
                className={scenario === "hot" ? "selected" : ""}
                onClick={() => applyPreset("hot")}
              >
                Hot year
              </button>
            </div>

            <div className="rd-slider-grid">
              <div className="rd-slider-item">
                <label htmlFor="temperature">
                  Temperature change
                  <strong>{temperature > 0 ? "+" : ""}{temperature}°C</strong>
                </label>
                <input
                  id="temperature"
                  type="range"
                  min="-2"
                  max="5"
                  step="1"
                  value={temperature}
                  onChange={(event) => {
                    setTemperature(Number(event.target.value));
                    setScenario("custom");
                  }}
                />
                <div className="rd-slider-labels">
                  <span>-2°C</span><span>+5°C</span>
                </div>
              </div>

              <div className="rd-slider-item">
                <label htmlFor="rainfall">
                  Rainfall change
                  <strong>{rainfall > 0 ? "+" : ""}{rainfall}%</strong>
                </label>
                <input
                  id="rainfall"
                  type="range"
                  min="-50"
                  max="50"
                  step="5"
                  value={rainfall}
                  onChange={(event) => {
                    setRainfall(Number(event.target.value));
                    setScenario("custom");
                  }}
                />
                <div className="rd-slider-labels">
                  <span>-50%</span><span>+50%</span>
                </div>
              </div>
            </div>

            <div className="rd-ranking-heading">
              <strong>Strategy ranking under this scenario</strong>
              <span>Prototype scores</span>
            </div>

            <div className="rd-ranking-list">
              {rankings.map((item, index) => (
                <div className="rd-ranking-row" key={item.name}>
                  <div className="rd-ranking-name">
                    <span>{index + 1}</span>
                    <strong>{item.name}</strong>
                  </div>
                  <div className="rd-ranking-track">
                    <div
                      className="rd-ranking-fill"
                      style={{ width: `${Math.min(100, item.score)}%` }}
                    />
                  </div>
                  <strong className="rd-ranking-score">
                    {Math.round(item.score)}
                  </strong>
                </div>
              ))}
            </div>

            <p className="rd-heat-note">
              These scores are demonstration calculations, not real
              agricultural model outputs or weather forecasts.
            </p>
          </div>
        </section>

        {/* EVIDENCE */}
        <section className="rd-section rd-evidence">
          <div className="rd-section-heading">
            <div>
              <p className="rd-eyebrow">TRANSPARENCY & EXPLANATION</p>
              <h2>Evidence & Confidence</h2>
              <p className="rd-section-description">
                Understand what supports a result and what information
                is still missing.
              </p>
            </div>

            <button
              type="button"
              className="rd-evidence-button"
              onClick={() => setEvidenceOpen(!evidenceOpen)}
              aria-expanded={evidenceOpen}
            >
              {evidenceOpen ? "Hide evidence" : "Explore evidence"} ↗
            </button>
          </div>

          {evidenceOpen && (
            <div className="rd-evidence-grid">
              {evidenceItems.map((item, index) => (
                <article className="rd-evidence-item" key={item.title}>
                  <span>0{index + 1}</span>
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </article>
              ))}
              <div className="rd-review-note">
                <strong>Needs local review</strong>
                <p>
                  Before using any rotation recommendation, verify
                  the results with local soil information and an
                  agricultural expert.
                </p>
              </div>
            </div>
          )}
        </section>

        {/* FOOTER */}
        <footer className="rd-footer">
          <span>ROOTWISE</span>
          <p>Know your land. Plan your future.</p>
          <p>M4 Dashboard · Prototype version</p>
        </footer>

      </div>
    </section>
  );
}
