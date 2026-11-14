
"use client";

import { useEffect, useState } from "react";
import type { SavedFarm } from "@/types/farm";
import { supabase } from "@/lib/supabase";
import {
  getSuggestedPathways,
  type RotationPathway,
} from "./rotationMatchmakerService";
import "./rotation-matchmaker.css";
import NasaInsights from "./NasaInsights";

type RotationMatchmakerProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm: SavedFarm | null;
  onGoToFarms?: () => void;
};

type CropPhase = {
  name: string;
  family: string;
  reason: string;
};

type RotationPathwayWithReasons = RotationPathway & {
  phase_reasons?: string[];
};

export default function RotationMatchmaker({
  isOpen,
  onClose,
  selectedFarm,
  onGoToFarms,
}: RotationMatchmakerProps) {
  const [pathways, setPathways] = useState<RotationPathway[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  const farmId = selectedFarm?.id;

  useEffect(() => {
    if (!isOpen || farmId == null) {
      setPathways([]);
      setError("");
      setLoading(false);
      return;
    }

    const validFarmId = farmId;
    let cancelled = false;

    async function loadPathways() {
      try {
        setLoading(true);
        setError("");

        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError) {
          throw sessionError;
        }

        if (!session?.access_token) {
          throw new Error(
            "Please sign in again to view crop rotation pathways."
          );
        }

        const results = await getSuggestedPathways(
          validFarmId,
          session.access_token
        );

        if (!cancelled) {
          setPathways(results);
        }
      } catch (err) {
        if (!cancelled) {
          setPathways([]);
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load crop rotation pathways."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPathways();

    return () => {
      cancelled = true;
    };
  }, [isOpen, farmId, retryCount]);

  const handleGoToFarms = () => {
    onClose();

    if (onGoToFarms) {
      onGoToFarms();
    } else {
      document
        .getElementById("your-farms")
        ?.scrollIntoView({ behavior: "smooth" });
    }
  };

  const getCropPhases = (
    pathway: RotationPathway
  ): CropPhase[] => {
    const pathwayData = pathway as RotationPathwayWithReasons;
    const cropDetails = pathwayData.crop_details ?? [];
    const phaseReasons = pathwayData.phase_reasons ?? [];

    return [0, 1, 2].map((index) => {
      const crop = cropDetails[index];

      return {
        name: crop?.name || "Crop selection required",
        family: crop?.family || "Family not available",
        reason:
          phaseReasons[index] ||
          "No explanation is available for this phase yet.",
      };
    });
  };

  if (!isOpen) return null;

  return (
    <div
      className="rw-modal rm-modal"
      style={{ padding: 0, placeItems: "stretch" }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
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
        <button
          className="rw-close"
          onClick={onClose}
          aria-label="Close"
        >
          ×
        </button>

        <div className="rm-workspace">
          <div className="rm-topbar">
            <button
              type="button"
              className="rm-back-home"
              onClick={onClose}
            >
              ← Back to Home
            </button>

            <div className="rm-brand">
              ROOTWISE<span>✦</span>
            </div>

            <div className="rm-topbar-spacer" />
          </div>

          <header className="rm-header" id="rm-top">
            <div>
              <div className="rm-kicker">
                ROOTWISE / MODULE 01
              </div>

              <h2>
                Rotation Matchmaker{" "}
                <span aria-hidden="true">✳</span>
              </h2>

              <p>
                Explore three-stage crop rotation pathways
                for your farm, one decision at a time.
              </p>
            </div>

            <div className="rm-disclaimer">
              <span aria-hidden="true">ⓘ</span>

              <div>
                <strong>Decision-support only</strong>

                <small>
                  Planning comparisons, not guaranteed recommendations.
                </small>
              </div>
            </div>
          </header>

          {!selectedFarm ? (
            <section className="rm-empty">
              <span className="rm-section-icon">⌖</span>

              <h3>Select a farm to begin</h3>

              <p>
                Save a farm profile or choose one under Your Farms.
                The Matchmaker will use the farm you currently have selected.
              </p>

              <button
                className="rm-action"
                onClick={handleGoToFarms}
              >
                Go to Your Farms
              </button>
            </section>
          ) : (
            <>
              <section
                className="rm-farm-panel"
                aria-labelledby="rm-farm-heading"
              >
                <div className="rm-farm-title">
                  <span className="rm-section-icon">⌖</span>

                  <div>
                    <h3 id="rm-farm-heading">
                      Selected farm
                    </h3>

                    <p>
                      These saved details will guide the rotation
                      pathways below.
                    </p>
                  </div>
                </div>

                <div className="rm-farm-name">
                  {selectedFarm.farm_name}
                </div>

                <div className="rm-farm-grid">
                  {[
                    [
                      "Area",
                      selectedFarm.area_acres != null
                        ? `${selectedFarm.area_acres} acres`
                        : "Not provided",
                    ],
                    [
                      "Soil type",
                      selectedFarm.soil_type || "Not provided",
                    ],
                    [
                      "Irrigation",
                      selectedFarm.irrigation || "Not provided",
                    ],
                    [
                      "Main crop",
                      selectedFarm.main_crop || "Not provided",
                    ],
                    [
                      "Sowing season",
                      selectedFarm.sowing_season || "Not provided",
                    ],
                    [
                      "Harvest period",
                      selectedFarm.harvest_period || "Not provided",
                    ],
                    [
                      "Previous sequence",
                      selectedFarm.previous_crop_sequence || "Not provided",
                    ],
                    [
                      "Farm priority",
                      selectedFarm.priority || "Not provided",
                    ],
                  ].map(([label, value]) => (
                    <div
                      className="rm-farm-detail"
                      key={label}
                    >
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>

                {selectedFarm.other_crops && (
                  <p className="rm-other-crops">
                    <strong>Other crops grown:</strong>{" "}
                    {selectedFarm.other_crops}
                  </p>
                )}
              </section>

              <section
                className="rm-section"
                id="rm-options"
              >
                <div className="rm-section-heading">
                  <span className="rm-section-icon">✿</span>

                  <div>
                    <div className="rm-kicker">
                      YOUR FARM, YOUR OPTIONS
                    </div>

                    <h3>Suggested Rotation Pathways</h3>

                    <p>
                      Explore three crop phases in each pathway.
                      Each phase includes its crop family and
                      the reason it is included. Check crop
                      suitability with local agricultural guidance.
                    </p>
                  </div>
                </div>

                <NasaInsights farmId={selectedFarm.id} />

                {loading && (
                  <div className="rm-empty">
                    <h3>
                      Preparing your crop rotation pathways...
                    </h3>

                    <p>
                      ROOTWISE is analysing your saved farm information.
                    </p>
                  </div>
                )}

                {!loading && error && (
                  <div className="rm-empty">
                    <h3>Unable to load pathways</h3>

                    <p>{error}</p>

                    <button
                      className="rm-action"
                      onClick={() =>
                        setRetryCount((count) => count + 1)
                      }
                    >
                      Try again
                    </button>
                  </div>
                )}

                {!loading && !error && pathways.length === 0 && (
                  <div className="rm-empty">
                    <h3>No pathways available</h3>

                    <p>
                      No crop rotation pathways were returned
                      for this farm. Check the farm details and
                      try again.
                    </p>

                    <button
                      className="rm-action"
                      onClick={() =>
                        setRetryCount((count) => count + 1)
                      }
                    >
                      Try again
                    </button>
                  </div>
                )}

                {!loading && !error && pathways.length > 0 && (
                  <div className="rm-pathway-grid">
                    {pathways.map((pathway) => {
                      const phases = getCropPhases(pathway);

                      return (
                        <article
                          className="rm-pathway-card"
                          key={pathway.number}
                        >
                          <div className="rm-card-top">
                            <span className="rm-option-tag">
                              PATHWAY {pathway.number}
                            </span>

                            <span className="rm-leaf-mark">
                              ✿
                            </span>
                          </div>

                          <h4>{pathway.title}</h4>

                          <div className="rm-sequence">
                            {pathway.sequence}
                          </div>

                          <div className="rm-card-block rm-phases-block">
                            <span>YOUR 3-CROP ROTATION PLAN</span>

                            
{pathway.strategy === "existing_rotation" ? (
  <div className="rm-card-block rm-phases-block">
    <span>SAVED CROP HISTORY</span>

    <div className="rm-history-note">
      This shows the crops recorded in your farm profile.
      Missing history is not automatically filled in.
    </div>

    {phases
      .filter((phase) => phase.name !== "Not recorded")
      .map((phase, index) => (
        <div className="rm-phase-card" key={index}>
          <div className="rm-phase-heading">
            <span className="rm-phase-number">
              0{index + 1}
            </span>
            <span>RECORDED CROP</span>
          </div>

          <h5>{phase.name}</h5>
          <small className="rm-phase-family">
            {phase.family}
          </small>
          <p className="rm-phase-reason">
            <strong>History:</strong>
            <br />
            {phase.reason}
          </p>
        </div>
      ))}

    {phases.every((phase) => phase.name === "Not recorded") && (
      <p>No previous crop history has been recorded.</p>
    )}
  </div>
) : (
  <div className="rm-card-block rm-phases-block">
    <span>YOUR 3-CROP ROTATION PLAN</span>

    <div className="rm-phase-list">
      {phases.map((phase, index) => (
        <div className="rm-phase-card" key={index}>
          <div className="rm-phase-heading">
            <span className="rm-phase-number">
              0{index + 1}
            </span>
            <span>PHASE {index + 1}</span>
          </div>

          <h5>{phase.name}</h5>

          <small className="rm-phase-family">
            {phase.family}
          </small>

          <p className="rm-phase-reason">
            <strong>Why this crop?</strong>
            <br />
            {phase.reason}
          </p>
        </div>
      ))}
    </div>
  </div>
)}

                          </div>

                          <div className="rm-card-block">
                            <span>What to explore</span>
                            <p>{pathway.purpose}</p>
                          </div>

                          {(pathway.benefits ?? []).length > 0 && (
                            <div className="rm-card-block">
                              <span>Potential benefits</span>

                              <ul>
                                {(pathway.benefits ?? []).map(
                                  (benefit, index) => (
                                    <li key={index}>{benefit}</li>
                                  )
                                )}
                              </ul>
                            </div>
                          )}

                          {(pathway.risks ?? []).length > 0 && (
                            <div className="rm-card-block">
                              <span>Potential limitations</span>

                              <ul>
                                {(pathway.risks ?? []).map(
                                  (risk, index) => (
                                    <li key={index}>{risk}</li>
                                  )
                                )}
                              </ul>
                            </div>
                          )}

                          <div className="rm-card-block rm-check-block">
                            <span>Before choosing, check</span>

                            <ul>
                              {(pathway.checks ?? []).map(
                                (check, index) => (
                                  <li key={index}>{check}</li>
                                )
                              )}
                            </ul>
                          </div>

                          {pathway.confidence && (
                            <div className="rm-card-block">
                              <span>Confidence</span>

                              {typeof pathway.confidence === "string" ? (
                                <p>{pathway.confidence}</p>
                              ) : (
                                <>
                                  <strong>
                                    {pathway.confidence.level ?? "Not rated"}
                                  </strong>

                                  {pathway.confidence.explanation && (
                                    <p>
                                      {pathway.confidence.explanation}
                                    </p>
                                  )}
                                </>
                              )}
                            </div>
                          )}
                        </article>
                      );
                    })}
                  </div>
                )}
              </section>
            </>
          )}

          <div className="rm-footer">
            <span>ROOTWISE · Rotation Matchmaker</span>

            <button
              onClick={() =>
                document
                  .getElementById("rm-top")
                  ?.scrollIntoView({ behavior: "smooth" })
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
