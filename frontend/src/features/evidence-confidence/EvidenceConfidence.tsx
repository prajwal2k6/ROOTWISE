
"use client";

import type { SavedFarm } from "@/types/farm";
import "./evidence-confidence.css";

type EvidenceConfidenceProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm?: SavedFarm | null;
};

const evidenceItems = [
  {
    number: "01",
    title: "Farm profile",
    source: "Farm details provided by the farmer",
    status: "Available",
    confidence: "High",
    description:
      "Farm location and basic field information provide the starting point for understanding local conditions.",
  },
  {
    number: "02",
    title: "Rainfall observations",
    source: "NASA POWER climate data",
    status: "Available",
    confidence: "Medium",
    description:
      "Historical rainfall patterns help identify seasonal wet and dry periods. Grid-based estimates may differ from actual field measurements.",
  },
  {
    number: "03",
    title: "Temperature observations",
    source: "NASA POWER climate data",
    status: "Available",
    confidence: "Medium",
    description:
      "Temperature observations provide regional climate context and help assess potential crop suitability.",
  },
  {
    number: "04",
    title: "Soil characteristics",
    source: "Farmer-provided information",
    status: "Needs input",
    confidence: "Low",
    description:
      "Soil type, pH and nutrient measurements are needed for a more reliable assessment of field conditions.",
  },
  {
    number: "05",
    title: "Crop history",
    source: "Farm records",
    status: "Needs input",
    confidence: "Low",
    description:
      "Previous crops and planting seasons help assess rotation suitability and identify repeated cropping patterns.",
  },
];

export default function EvidenceConfidence({
  isOpen,
  onClose,
  selectedFarm,
}: EvidenceConfidenceProps) {
  if (!isOpen) return null;

  const farmName =
    selectedFarm && "name" in selectedFarm
      ? String(selectedFarm.name || "Selected farm")
      : "Farm profile not selected";

  return (
    <div className="ec-page-overlay" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <div
        className="ec-page"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ec-heading"
      >
        <header className="ec-header">
          <div>
            <div className="ec-eyebrow">ROOTWISE / FEATURE 05</div>
            <h1 id="ec-heading">Evidence & Confidence</h1>
            <p>
              Understand the information behind your farm insights,
              where it comes from and what still needs attention.
            </p>
          </div>

          <button
            className="ec-close"
            onClick={onClose}
            aria-label="Close evidence page"
          >
            ×
          </button>
        </header>

        <div className="ec-content">
          <section className="ec-intro-card">
            <div>
              <span className="ec-section-label">YOUR EVIDENCE REPORT</span>
              <h2>Insights should be transparent.</h2>
              <p>
                ROOTWISE brings together farm information and environmental
                observations. This page explains how much supporting
                information is available and where further inputs are needed.
              </p>
            </div>
            <div className="ec-report-mark">05</div>
          </section>

          <section className="ec-farm-strip">
            <div>
              <span className="ec-muted-label">CURRENT FARM</span>
              <strong>{farmName}</strong>
            </div>
            <div>
              <span className="ec-muted-label">REPORT STATUS</span>
              <strong className="ec-demo-status">Illustrative preview</strong>
            </div>
          </section>

          <section className="ec-section">
            <div className="ec-section-heading">
              <div>
                <span className="ec-section-label">01 / OVERVIEW</span>
                <h2>Evidence at a glance</h2>
                <p>A quick view of the information represented in this demo.</p>
              </div>
            </div>

            <div className="ec-stats-grid">
              <div className="ec-stat-card">
                <span className="ec-stat-number">05</span>
                <span className="ec-stat-title">Evidence categories</span>
                <span className="ec-stat-note">Included in this preview</span>
              </div>
              <div className="ec-stat-card">
                <span className="ec-stat-number">03</span>
                <span className="ec-stat-title">Categories represented</span>
                <span className="ec-stat-note">Farm and climate information</span>
              </div>
              <div className="ec-stat-card">
                <span className="ec-stat-number">02</span>
                <span className="ec-stat-title">Data gaps</span>
                <span className="ec-stat-note">More farm inputs needed</span>
              </div>
            </div>

            <div className="ec-demo-notice">
              <span>ⓘ</span>
              <p>
                These are illustrative demo values, not measured confidence
                scores or verified observations from your farm. Actual
                assessments will depend on connected data and farm inputs.
              </p>
            </div>
          </section>

          <section className="ec-section">
            <div className="ec-section-heading">
              <div>
                <span className="ec-section-label">02 / DATA SOURCES</span>
                <h2>What supports the insights?</h2>
                <p>
                  Each source contributes a different piece of information.
                </p>
              </div>
            </div>

            <div className="ec-evidence-list">
              {evidenceItems.map((item) => (
                <article className="ec-evidence-card" key={item.number}>
                  <div className="ec-evidence-number">{item.number}</div>
                  <div className="ec-evidence-main">
                    <h3>{item.title}</h3>
                    <span className="ec-source">{item.source}</span>
                    <p>{item.description}</p>
                  </div>
                  <div className="ec-evidence-meta">
                    <span
                      className={`ec-status ${
                        item.status === "Available" ? "available" : "missing"
                      }`}
                    >
                      {item.status}
                    </span>
                    <span
                      className={`ec-confidence ${item.confidence.toLowerCase()}`}
                    >
                      {item.confidence} confidence
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="ec-section">
            <div className="ec-section-heading">
              <div>
                <span className="ec-section-label">03 / DATA GAPS</span>
                <h2>What information is missing?</h2>
                <p>
                  Better farm-level information can improve the relevance
                  of recommendations.
                </p>
              </div>
            </div>

            <div className="ec-gaps-grid">
              <div className="ec-gap-card">
                <span className="ec-gap-icon">01</span>
                <h3>Soil test results</h3>
                <p>
                  Soil pH, organic matter and nutrient measurements can
                  strengthen crop suitability assessments.
                </p>
                <span className="ec-gap-tag">Farmer input needed</span>
              </div>
              <div className="ec-gap-card">
                <span className="ec-gap-icon">02</span>
                <h3>Previous crop records</h3>
                <p>
                  Crop names, growing seasons and previous rotation details
                  help assess long-term field patterns.
                </p>
                <span className="ec-gap-tag">Farm records needed</span>
              </div>
              <div className="ec-gap-card">
                <span className="ec-gap-icon">03</span>
                <h3>On-field measurements</h3>
                <p>
                  Local rainfall gauges and soil-moisture readings can
                  complement regional environmental datasets.
                </p>
                <span className="ec-gap-tag">Additional observations</span>
              </div>
            </div>
          </section>

          <section className="ec-section">
            <div className="ec-section-heading">
              <div>
                <span className="ec-section-label">04 / TRANSPARENCY</span>
                <h2>Limitations to keep in mind</h2>
                <p>
                  Environmental data is useful, but it cannot describe
                  every condition on an individual farm.
                </p>
              </div>
            </div>

            <div className="ec-limitations">
              <div>
                <span className="ec-limit-icon">↗</span>
                <div>
                  <h3>Regional data is not field data</h3>
                  <p>
                    Satellite and gridded climate datasets represent broader
                    areas. Actual conditions may vary within a farm.
                  </p>
                </div>
              </div>
              <div>
                <span className="ec-limit-icon">!</span>
                <div>
                  <h3>Historical patterns are not forecasts</h3>
                  <p>
                    Past rainfall and temperature patterns can provide
                    context, but they do not guarantee future conditions.
                  </p>
                </div>
              </div>
              <div>
                <span className="ec-limit-icon">◇</span>
                <div>
                  <h3>Recommendations depend on available inputs</h3>
                  <p>
                    Missing soil information, crop records or local
                    measurements can reduce the reliability of an assessment.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="ec-bottom-card">
            <span className="ec-section-label">ROOTWISE PRINCIPLE</span>
            <h2>Know what the data says. Know what it doesn't.</h2>
            <p>
              Our goal is to make agricultural insights understandable,
              transparent and grounded in available evidence.
            </p>
            <button className="ec-back-button" onClick={onClose}>
              ← Back to ROOTWISE
            </button>
          </section>

          <footer className="ec-footer">
            ROOTWISE · Evidence before assumptions
          </footer>
        </div>
      </div>
    </div>
  );
}
