
"use client";

import { useState } from "react";
import type { SavedFarm } from "@/types/farm";
import { getSoilStressDetails } from "./soilStressCalendarService";
import "./soil-stress-calendar.css";

type SoilStressCalendarProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm?: SavedFarm | null;
};

type StressMonth = {
  month: string;
  short: string;
  rainfall: number;
  temperature: number;
  moisture: number;
  risk: number;
  status: "Low" | "Moderate" | "High";
  note: string;
  action: string;
};

const months: StressMonth[] = [
  {
    month: "January",
    short: "JAN",
    rainfall: 12,
    temperature: 27,
    moisture: 34,
    risk: 58,
    status: "Moderate",
    note: "Low rainfall may gradually reduce available soil moisture.",
    action: "Check soil moisture before sowing or increasing irrigation.",
  },
  {
    month: "February",
    short: "FEB",
    rainfall: 8,
    temperature: 29,
    moisture: 27,
    risk: 72,
    status: "High",
    note: "A relatively dry period may increase moisture stress.",
    action: "Plan irrigation carefully and monitor moisture near the root zone.",
  },
  {
    month: "March",
    short: "MAR",
    rainfall: 18,
    temperature: 31,
    moisture: 30,
    risk: 66,
    status: "Moderate",
    note: "Rising temperatures can increase water demand.",
    action: "Review crop water requirements and avoid unnecessary water loss.",
  },
  {
    month: "April",
    short: "APR",
    rainfall: 42,
    temperature: 30,
    moisture: 43,
    risk: 42,
    status: "Moderate",
    note: "Changing rainfall patterns may create uneven moisture conditions.",
    action: "Observe drainage and check whether rainfall is reaching the root zone.",
  },
  {
    month: "May",
    short: "MAY",
    rainfall: 110,
    temperature: 28,
    moisture: 61,
    risk: 24,
    status: "Low",
    note: "Pre-monsoon rainfall may improve soil moisture availability.",
    action: "Prepare drainage channels and inspect water storage arrangements.",
  },
  {
    month: "June",
    short: "JUN",
    rainfall: 260,
    temperature: 25,
    moisture: 78,
    risk: 18,
    status: "Low",
    note: "Higher rainfall may improve moisture but can also cause waterlogging.",
    action: "Check field drainage and protect young crops from excess water.",
  },
  {
    month: "July",
    short: "JUL",
    rainfall: 310,
    temperature: 24,
    moisture: 86,
    risk: 22,
    status: "Low",
    note: "Continued rainfall may keep soils wet for extended periods.",
    action: "Monitor waterlogging, erosion and nutrient runoff.",
  },
  {
    month: "August",
    short: "AUG",
    rainfall: 280,
    temperature: 24,
    moisture: 82,
    risk: 25,
    status: "Low",
    note: "High moisture conditions may affect root aeration in poorly drained fields.",
    action: "Inspect drainage and watch for signs of root stress.",
  },
  {
    month: "September",
    short: "SEP",
    rainfall: 190,
    temperature: 25,
    moisture: 70,
    risk: 32,
    status: "Moderate",
    note: "Rainfall may become less consistent as the season changes.",
    action: "Track rainfall and reassess water needs before the next crop stage.",
  },
  {
    month: "October",
    short: "OCT",
    rainfall: 95,
    temperature: 26,
    moisture: 55,
    risk: 40,
    status: "Moderate",
    note: "Declining rainfall can create a gradual drop in soil moisture.",
    action: "Review stored water and plan irrigation for the coming weeks.",
  },
  {
    month: "November",
    short: "NOV",
    rainfall: 28,
    temperature: 25,
    moisture: 40,
    risk: 55,
    status: "Moderate",
    note: "Reduced rainfall may affect crops that need consistent moisture.",
    action: "Check soil conditions before choosing the next crop.",
  },
  {
    month: "December",
    short: "DEC",
    rainfall: 15,
    temperature: 26,
    moisture: 32,
    risk: 63,
    status: "Moderate",
    note: "Drier conditions may begin to increase water requirements.",
    action: "Plan water availability and monitor moisture during crop establishment.",
  },
];

const seasons = [
  { name: "All year", months: months.map((item) => item.short) },
  { name: "Winter", months: ["DEC", "JAN", "FEB"] },
  { name: "Summer", months: ["MAR", "APR", "MAY"] },
  { name: "Monsoon", months: ["JUN", "JUL", "AUG", "SEP"] },
  { name: "Post-monsoon", months: ["OCT", "NOV"] },
];

function getStatusClass(status: string) {
  return status.toLowerCase();
}

export default function SoilStressCalendar({
  isOpen,
  onClose,
  selectedFarm,
}: SoilStressCalendarProps) {
  const [selectedMonth, setSelectedMonth] = useState("FEB");
  const [selectedSeason, setSelectedSeason] = useState("All year");

  if (!isOpen) return null;

  const feature = getSoilStressDetails();
  const activeSeason =
    seasons.find((season) => season.name === selectedSeason) ?? seasons[0];

  const visibleMonths = months.filter((month) =>
    activeSeason.months.includes(month.short)
  );

  const selected =
    months.find((month) => month.short === selectedMonth) ?? months[1];

  const averageRisk = Math.round(
    visibleMonths.reduce((sum, month) => sum + month.risk, 0) /
      visibleMonths.length
  );

  const highRiskCount = visibleMonths.filter(
    (month) => month.status === "High"
  ).length;

  const moderateCount = visibleMonths.filter(
    (month) => month.status === "Moderate"
  ).length;

  function changeSeason(seasonName: string) {
    setSelectedSeason(seasonName);
    const season = seasons.find((item) => item.name === seasonName);
    if (season && !season.months.includes(selectedMonth)) {
      setSelectedMonth(season.months[0]);
    }
  }

  return (
    <div
      className="rw-modal ssc-modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="ssc-page"
        role="dialog"
        aria-modal="true"
        aria-label="Soil Stress Calendar"
      >
        <header className="ssc-header">
          <button className="ssc-brand" onClick={onClose}>
            <span className="ssc-brand-mark">R</span>
            <span>ROOTWISE</span>
          </button>

          <div className="ssc-header-right">
            <span className="ssc-header-label">FIELD INTELLIGENCE</span>
            <button
              className="ssc-close"
              onClick={onClose}
              aria-label="Close Soil Stress Calendar"
            >
              ×
            </button>
          </div>
        </header>

        <main className="ssc-content">
          <div className="ssc-eyebrow">
            <span>03</span>
            <span className="ssc-eyebrow-line" />
            SOIL STRESS CALENDAR
          </div>

          <section className="ssc-intro">
            <div className="ssc-intro-copy">
              <h1>
                Know when your
                <br />
                <em>land needs attention.</em>
              </h1>
              <p>
                Spot seasonal windows that may bring low soil moisture, high
                temperatures or irregular rainfall — before planning your next
                crop.
              </p>
              <div className="ssc-farm-label">
                <span className="ssc-farm-dot" />
                {selectedFarm
  ? `Viewing: ${selectedFarm.name || "Selected farm"}`
  : "Exploring seasonal conditions"}
              </div>
            </div>

            <div className="ssc-intro-art" aria-hidden="true">
              <div className="ssc-art-sun" />
              <div className="ssc-art-cloud">☁</div>
              <div className="ssc-art-hill ssc-art-hill-back" />
              <div className="ssc-art-hill ssc-art-hill-front" />
              <div className="ssc-art-field">
                <span />
                <span />
                <span />
                <span />
              </div>
              <div className="ssc-art-plant">♧</div>
              <div className="ssc-art-caption">READ THE SEASONS</div>
            </div>
          </section>

          <div className="ssc-demo-note">
            <span className="ssc-demo-icon">i</span>
            <span>
              <strong>Illustrative preview.</strong> The values shown are demo
              data, not live measurements from your farm.
            </span>
          </div>

          <section className="ssc-overview">
            <div className="ssc-section-heading">
              <div>
                <span className="ssc-kicker">SEASONAL OVERVIEW</span>
                <h2>A year of changing conditions</h2>
                <p>
                  Explore potentially vulnerable periods by season or month.
                </p>
              </div>
              <div className="ssc-season-select">
                <label htmlFor="ssc-season">VIEW SEASON</label>
                <select
                  id="ssc-season"
                  value={selectedSeason}
                  onChange={(event) => changeSeason(event.target.value)}
                >
                  {seasons.map((season) => (
                    <option key={season.name} value={season.name}>
                      {season.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="ssc-summary-grid">
              <div className="ssc-summary-card">
                <span>AVERAGE STRESS INDEX</span>
                <strong>{averageRisk}<small>/100</small></strong>
                <div className="ssc-summary-track">
                  <div style={{ width: `${averageRisk}%` }} />
                </div>
                <p>Across the selected period</p>
              </div>
              <div className="ssc-summary-card">
                <span>HIGH-STRESS MONTHS</span>
                <strong>{highRiskCount.toString().padStart(2, "0")}</strong>
                <p>Months needing closer attention</p>
              </div>
              <div className="ssc-summary-card">
                <span>MODERATE-STRESS MONTHS</span>
                <strong>{moderateCount.toString().padStart(2, "0")}</strong>
                <p>Months worth monitoring</p>
              </div>
            </div>

            <div className="ssc-calendar-panel">
              <div className="ssc-calendar-top">
                <div>
                  <h3>Monthly stress outlook</h3>
                  <p>Select a month to explore its conditions.</p>
                </div>
                <div className="ssc-legend">
                  <span><i className="ssc-dot low" /> Low</span>
                  <span><i className="ssc-dot moderate" /> Moderate</span>
                  <span><i className="ssc-dot high" /> High</span>
                </div>
              </div>

              <div className="ssc-month-grid">
                {visibleMonths.map((month) => (
                  <button
                    key={month.short}
                    className={`ssc-month-card ${getStatusClass(month.status)} ${
                      selectedMonth === month.short ? "selected" : ""
                    }`}
                    onClick={() => setSelectedMonth(month.short)}
                    aria-pressed={selectedMonth === month.short}
                  >
                    <span className="ssc-month-name">{month.short}</span>
                    <span className="ssc-month-indicator" />
                    <strong>{month.risk}</strong>
                    <span className="ssc-month-status">{month.status}</span>
                  </button>
                ))}
              </div>

              <div className="ssc-calendar-foot">
                <span>LOWER INDEX = FEWER POTENTIAL STRESS SIGNALS</span>
                <span>DEMO INDEX · 0–100</span>
              </div>
            </div>
          </section>

          <section className="ssc-detail-section">
            <div className="ssc-detail-heading">
              <div>
                <span className="ssc-kicker">MONTHLY BREAKDOWN</span>
                <h2>What is happening in {selected.month}?</h2>
                <p>
                  Review the environmental indicators and possible actions for
                  this period.
                </p>
              </div>
              <span className={`ssc-status-pill ${getStatusClass(selected.status)}`}>
                <i />
                {selected.status} stress
              </span>
            </div>

            <div className="ssc-detail-grid">
              <div className="ssc-indicators">
                <div className="ssc-indicator-card">
                  <div className="ssc-indicator-icon rainfall">☂</div>
                  <div className="ssc-indicator-info">
                    <span>RAINFALL</span>
                    <strong>{selected.rainfall}<small> mm</small></strong>
                    <p>Illustrative monthly total</p>
                  </div>
                </div>
                <div className="ssc-indicator-card">
                  <div className="ssc-indicator-icon temperature">☼</div>
                  <div className="ssc-indicator-info">
                    <span>TEMPERATURE</span>
                    <strong>{selected.temperature}<small> °C</small></strong>
                    <p>Illustrative monthly average</p>
                  </div>
                </div>
                <div className="ssc-indicator-card">
                  <div className="ssc-indicator-icon moisture">◉</div>
                  <div className="ssc-indicator-info">
                    <span>SOIL MOISTURE</span>
                    <strong>{selected.moisture}<small> / 100</small></strong>
                    <p>Illustrative moisture index</p>
                  </div>
                </div>
              </div>

              <div className="ssc-insight-card">
                <span className="ssc-kicker">ROOTWISE OBSERVATION</span>
                <div className="ssc-insight-score">
                  <strong>{selected.risk}</strong>
                  <span>STRESS INDEX</span>
                </div>
                <p>{selected.note}</p>
                <div className="ssc-insight-divider" />
                <span className="ssc-kicker">SUGGESTED FIELD ACTION</span>
                <p className="ssc-action-text">{selected.action}</p>
              </div>
            </div>
          </section>

          <section className="ssc-planning">
            <div className="ssc-planning-copy">
              <span className="ssc-kicker">PLAN AHEAD</span>
              <h2>Prepare for the season, not just the day.</h2>
              <p>
                Use seasonal indicators alongside field observations, crop
                requirements and local weather information before making
                irrigation or crop-planning decisions.
              </p>
            </div>
            <div className="ssc-planning-list">
              <div><span>01</span> Monitor soil moisture regularly</div>
              <div><span>02</span> Check rainfall and drainage patterns</div>
              <div><span>03</span> Match crop needs to water availability</div>
            </div>
          </section>

          <footer className="ssc-footer">
            <div>
              <strong>ROOTWISE</strong>
              <span>Understand your land. Plan with confidence.</span>
            </div>
            <button onClick={onClose}>← Back to experience</button>
          </footer>
        </main>
      </div>
    </div>
  );
}
