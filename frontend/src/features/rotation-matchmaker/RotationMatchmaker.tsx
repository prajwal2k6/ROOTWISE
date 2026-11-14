"use client";

import type { SavedFarm } from "@/types/farm";
import { getSuggestedPathways } from "./rotationMatchmakerService";
import "./rotation-matchmaker.css";

type RotationMatchmakerProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm: SavedFarm | null;
  onGoToFarms?: () => void;
};

export default function RotationMatchmaker({
  isOpen,
  onClose,
  selectedFarm,
  onGoToFarms,
}: RotationMatchmakerProps) {
  if (!isOpen) return null;

  const pathways = getSuggestedPathways();

  const handleGoToFarms = () => {
    onClose();
    if (onGoToFarms) {
      onGoToFarms();
    } else {
      document.getElementById("your-farms")?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div
      className="rw-modal rm-modal"
      style={{ padding: 0, placeItems: "stretch" }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="rw-modalbox rm-modalbox"
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
        <div className="rm-workspace">
          <div className="rm-topbar">
            <button type="button" className="rm-back-home" onClick={onClose}>
              ← Back to Home
            </button>
            <div className="rm-brand">
              ROOTWISE<span>✦</span>
            </div>
            <div className="rm-topbar-spacer" />
          </div>
          <header className="rm-header" id="rm-top">
            <div>
              <div className="rm-kicker">ROOTWISE / MODULE 01</div>
              <h2>
                Rotation Matchmaker <span aria-hidden="true">✳</span>
              </h2>
              <p>Explore crop-rotation pathways for your farm, one decision at a time.</p>
            </div>
            <div className="rm-disclaimer">
              <span aria-hidden="true">ⓘ</span>
              <div>
                <strong>Decision-support only</strong>
                <small>Planning comparisons, not guaranteed recommendations.</small>
              </div>
            </div>
          </header>

          {!selectedFarm ? (
            <section className="rm-empty">
              <span className="rm-section-icon">⌖</span>
              <h3>Select a farm to begin</h3>
              <p>
                Save a farm profile or choose one under Your Farms. The Matchmaker will use
                the farm you currently have selected.
              </p>
              <button className="rm-action" onClick={handleGoToFarms}>
                Go to Your Farms
              </button>
            </section>
          ) : (
            <>
              <section className="rm-farm-panel" aria-labelledby="rm-farm-heading">
                <div className="rm-farm-title">
                  <span className="rm-section-icon">⌖</span>
                  <div>
                    <h3 id="rm-farm-heading">Selected farm</h3>
                    <p>These saved details will guide the rotation pathways below.</p>
                  </div>
                </div>
                <div className="rm-farm-name">{selectedFarm.farm_name}</div>
                <div className="rm-farm-grid">
                  {[
                    [
                      "Area",
                      selectedFarm.area_acres != null
                        ? `${selectedFarm.area_acres} acres`
                        : "Not provided",
                    ],
                    ["Soil type", selectedFarm.soil_type || "Not provided"],
                    ["Irrigation", selectedFarm.irrigation || "Not provided"],
                    ["Main crop", selectedFarm.main_crop || "Not provided"],
                    ["Sowing season", selectedFarm.sowing_season || "Not provided"],
                    ["Harvest period", selectedFarm.harvest_period || "Not provided"],
                    [
                      "Previous sequence",
                      selectedFarm.previous_crop_sequence || "Not provided",
                    ],
                    ["Farm priority", selectedFarm.priority || "Not provided"],
                  ].map(([label, value]) => (
                    <div className="rm-farm-detail" key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>
                {selectedFarm.other_crops && (
                  <p className="rm-other-crops">
                    <strong>Other crops grown:</strong> {selectedFarm.other_crops}
                  </p>
                )}
              </section>

              <section className="rm-section" id="rm-options">
                <div className="rm-section-heading">
                  <span className="rm-section-icon">✿</span>
                  <div>
                    <div className="rm-kicker">YOUR FARM, YOUR OPTIONS</div>
                    <h3>Suggested Rotation Pathways</h3>
                    <p>
                      Rotation options based on your soil, crop history, irrigation and farm
                      priority. Check specific crop suitability with local agricultural guidance.
                    </p>
                  </div>
                </div>
                <div className="rm-pathway-grid">
                  {pathways.map((pathway) => (
                    <article className="rm-pathway-card" key={pathway.number}>
                      <div className="rm-card-top">
                        <span className="rm-option-tag">PATHWAY {pathway.number}</span>
                        <span className="rm-leaf-mark">✿</span>
                      </div>
                      <h4>{pathway.title}</h4>
                      <div className="rm-sequence">{pathway.sequence}</div>
                      <div className="rm-card-block">
                        <span>What to explore</span>
                        <p>{pathway.purpose}</p>
                      </div>
                      <div className="rm-card-block rm-check-block">
                        <span>Before choosing, check</span>
                        <p>{pathway.checks}</p>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            </>
          )}
          <div className="rm-footer">
            <span>ROOTWISE · Rotation Matchmaker</span>
            <button
              onClick={() =>
                document.getElementById("rm-top")?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Back to top ↑
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
