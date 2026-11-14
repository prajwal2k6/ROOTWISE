"use client";

import type { SavedFarm } from "@/types/farm";
import { getEvidenceConfidenceDetails } from "./evidenceConfidenceService";
import "./evidence-confidence.css";

type EvidenceConfidenceProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm?: SavedFarm | null;
};

export default function EvidenceConfidence({
  isOpen,
  onClose,
}: EvidenceConfidenceProps) {
  if (!isOpen) return null;

  const feature = getEvidenceConfidenceDetails();

  return (
    <div
      className="rw-modal ec-modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="rw-modalbox">
        <button className="rw-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className="rw-step-label ec-badge">ROOTWISE FEATURE</div>
        <h2>{feature.name}</h2>
        <p>{feature.detail}</p>
        <button className="rw-submit" onClick={onClose}>
          Back to experience
        </button>
      </div>
    </div>
  );
}
