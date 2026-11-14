"use client";

import type { SavedFarm } from "@/types/farm";
import { getLandMemoryDetails } from "./landMemoryService";
import "./land-memory.css";

type LandMemoryProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm?: SavedFarm | null;
};

export default function LandMemory({
  isOpen,
  onClose,
}: LandMemoryProps) {
  if (!isOpen) return null;

  const feature = getLandMemoryDetails();

  return (
    <div
      className="rw-modal lm-modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="rw-modalbox">
        <button className="rw-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className="rw-step-label lm-badge">ROOTWISE FEATURE</div>
        <h2>{feature.name}</h2>
        <p>{feature.detail}</p>
        <button className="rw-submit" onClick={onClose}>
          Back to experience
        </button>
      </div>
    </div>
  );
}
