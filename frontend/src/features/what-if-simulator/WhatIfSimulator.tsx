"use client";

import { useState } from "react";
import type { SavedFarm } from "@/types/farm";
import { MONSOON_OPTIONS } from "./whatIfSimulatorService";
import "./what-if-simulator.css";

type WhatIfSimulatorProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm: SavedFarm | null;
  onGoToFarms?: () => void;
};

export default function WhatIfSimulator({
  isOpen,
  onClose,
  selectedFarm,
  onGoToFarms,
}: WhatIfSimulatorProps) {
  const [scenarioRainfall, setScenarioRainfall] = useState(0);
  const [scenarioTemperature, setScenarioTemperature] = useState(0);
  const [scenarioMonsoon, setScenarioMonsoon] = useState("Usual timing");

  if (!isOpen) return null;

  const handleGoToFarms = () => {
    onClose();
    if (onGoToFarms) {
      onGoToFarms();
    } else {
      document.getElementById("your-farms")?.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleReset = () => {
    setScenarioRainfall(0);
    setScenarioTemperature(0);
    setScenarioMonsoon("Usual timing");
  };

  return (
    <div
      className="rw-modal wi-modal"
      style={{ padding: 0, placeItems: "stretch" }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="rw-modalbox wi-modalbox"
        style={{
          width: "100%",
          maxWidth: "none",
          height: "100dvh",
          maxHeight: "none",
          overflowY: "auto",
          borderRadius: 0,
          padding: 0,
        }}
      >
        <button className="rw-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className="wi-workspace">
          <div className="wi-topbar">
            <button type="button" className="wi-back-home" onClick={onClose}>
              ← Back to Home
            </button>
            <div className="wi-brand">
              ROOT<span>WISE</span>
            </div>
            <div />
          </div>

          <header className="wi-header">
            <div>
              <div className="wi-kicker">ROOTWISE / MODULE 02</div>
              <h2>
                What-if Simulator <span>✳</span>
              </h2>
              <p>Change the season assumptions and explore what you may want to consider for your farm.</p>
            </div>
            <div className="wi-notice">
              <span>ⓘ</span>
              <div>
                <strong>Hypothetical scenario</strong>
                <small>These controls are for exploration only—not a weather forecast or crop-yield prediction.</small>
              </div>
            </div>
          </header>

          {!selectedFarm ? (
            <section className="wi-empty">
              <div className="wi-icon">⌖</div>
              <h3>Select a farm to begin</h3>
              <p>Save a farm profile or choose one under Your Farms. The simulator will display the farm you currently have selected.</p>
              <button type="button" className="wi-primary" onClick={handleGoToFarms}>
                Go to Your Farms
              </button>
            </section>
          ) : (
            <>
              <section className="wi-farm-strip">
                <div className="wi-farm-symbol">⌖</div>
                <div className="wi-farm-meta">
                  <span>SCENARIO FARM</span>
                  <strong>{selectedFarm.farm_name}</strong>
                  <small>
                    {selectedFarm.main_crop || "Main crop not specified"} · {selectedFarm.area_acres.toFixed(2)} acres
                  </small>
                </div>
                <div className="wi-farm-meta wi-farm-soil">
                  <span>SOIL</span>
                  <strong>{selectedFarm.soil_type || "Not provided"}</strong>
                </div>
                <div className="wi-farm-meta wi-farm-water">
                  <span>IRRIGATION</span>
                  <strong>{selectedFarm.irrigation || "Not provided"}</strong>
                </div>
              </section>

              <section className="wi-controls-section">
                <div className="wi-section-heading">
                  <div className="wi-icon">☼</div>
                  <div>
                    <div className="wi-kicker">BUILD A SCENARIO</div>
                    <h3>Adjust seasonal conditions</h3>
                    <p>Move one or more controls away from the baseline to explore a different set of assumptions.</p>
                  </div>
                </div>

                <div className="wi-controls-grid">
                  <article className="wi-control-card">
                    <div className="wi-control-heading">
                      <div>
                        <span className="wi-control-label">RAINFALL CHANGE</span>
                        <h4>Rainfall assumption</h4>
                      </div>
                      <strong>
                        {scenarioRainfall > 0 ? "+" : ""}
                        {scenarioRainfall}%
                      </strong>
                    </div>
                    <input
                      aria-label="Rainfall change percentage"
                      type="range"
                      min="-50"
                      max="30"
                      step="5"
                      value={scenarioRainfall}
                      onChange={(event) => setScenarioRainfall(Number(event.target.value))}
                    />
                    <div className="wi-range-labels">
                      <span>50% lower</span>
                      <span>Baseline</span>
                      <span>30% higher</span>
                    </div>
                    <p>Change the assumed seasonal rainfall relative to a usual baseline. This is not a measured rainfall value.</p>
                  </article>

                  <article className="wi-control-card">
                    <div className="wi-control-heading">
                      <div>
                        <span className="wi-control-label">TEMPERATURE CHANGE</span>
                        <h4>Temperature assumption</h4>
                      </div>
                      <strong>+{scenarioTemperature.toFixed(1)}°C</strong>
                    </div>
                    <input
                      aria-label="Temperature change in degrees Celsius"
                      type="range"
                      min="0"
                      max="4"
                      step="0.5"
                      value={scenarioTemperature}
                      onChange={(event) => setScenarioTemperature(Number(event.target.value))}
                    />
                    <div className="wi-range-labels">
                      <span>Baseline</span>
                      <span>+2°C</span>
                      <span>+4°C</span>
                    </div>
                    <p>Explore a warmer-season assumption compared with the baseline. It is not a local temperature forecast.</p>
                  </article>

                  <article className="wi-control-card wi-monsoon-card">
                    <div className="wi-control-heading">
                      <div>
                        <span className="wi-control-label">MONSOON TIMING</span>
                        <h4>Season start assumption</h4>
                      </div>
                      <strong>◷</strong>
                    </div>
                    <select
                      aria-label="Monsoon timing assumption"
                      value={scenarioMonsoon}
                      onChange={(event) => setScenarioMonsoon(event.target.value)}
                    >
                      {MONSOON_OPTIONS.map((opt) => (
                        <option key={opt}>{opt}</option>
                      ))}
                    </select>
                    <p>Shift the assumed monsoon start to consider how your planning calendar may need to adapt.</p>
                  </article>
                </div>
                <button type="button" className="wi-reset" onClick={handleReset}>
                  ↺ Reset to baseline
                </button>
              </section>

              <section className="wi-result-section">
                <div className="wi-section-heading">
                  <div className="wi-icon">✿</div>
                  <div>
                    <div className="wi-kicker">YOUR CURRENT SCENARIO</div>
                    <h3>Scenario overview</h3>
                    <p>A clear readout of the assumptions you selected—without treating them as predictions.</p>
                  </div>
                </div>
                <div className="wi-result-grid">
                  <div className="wi-result-card">
                    <span>RAINFALL</span>
                    <strong>
                      {scenarioRainfall > 0 ? "+" : ""}
                      {scenarioRainfall}%
                    </strong>
                    <small>
                      {scenarioRainfall === 0
                        ? "Baseline assumption"
                        : scenarioRainfall < 0
                        ? "Lower than baseline"
                        : "Higher than baseline"}
                    </small>
                  </div>
                  <div className="wi-result-card">
                    <span>TEMPERATURE</span>
                    <strong>+{scenarioTemperature.toFixed(1)}°C</strong>
                    <small>{scenarioTemperature === 0 ? "Baseline assumption" : "Warmer than baseline"}</small>
                  </div>
                  <div className="wi-result-card">
                    <span>MONSOON</span>
                    <strong className="wi-result-monsoon">{scenarioMonsoon}</strong>
                    <small>Timing assumption</small>
                  </div>
                </div>
                <div className="wi-interpretation">
                  <div className="wi-interpretation-title">
                    <span>✧</span>
                    <strong>Questions to consider for this scenario</strong>
                  </div>
                  {scenarioRainfall < 0 && (
                    <p>With lower assumed rainfall, consider checking water availability, irrigation access and the water requirements of each crop under consideration.</p>
                  )}
                  {scenarioRainfall > 0 && (
                    <p>With higher assumed rainfall, consider field drainage, waterlogging sensitivity and whether sowing or field operations may need flexibility.</p>
                  )}
                  {scenarioRainfall === 0 && (
                    <p>Rainfall remains at the baseline assumption. You can change it to explore a drier or wetter seasonal scenario.</p>
                  )}
                  {scenarioTemperature > 0 && (
                    <p>A warmer temperature assumption makes it useful to review crop heat sensitivity, local sowing windows and access to water during warmer periods.</p>
                  )}
                  {scenarioTemperature === 0 && (
                    <p>Temperature remains at the baseline assumption. Increase it to explore a warmer-season scenario.</p>
                  )}
                  {scenarioMonsoon !== "Usual timing" && (
                    <p>{scenarioMonsoon} may affect the timing of land preparation and sowing. Check local seasonal advisories before changing farm operations.</p>
                  )}
                  {scenarioMonsoon === "Usual timing" && (
                    <p>Monsoon timing remains at the usual baseline assumption.</p>
                  )}
                </div>
              </section>
            </>
          )}
          <footer className="wi-footer">
            <span>ROOTWISE · What-if Simulator · Illustrative assumptions only</span>
            <button
              type="button"
              onClick={() => document.querySelector(".wi-workspace")?.scrollTo({ top: 0, behavior: "smooth" })}
            >
              Back to top ↑
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
