"use client";

import type { SavedFarm } from "@/types/farm";
import { getFarmerDashboardDetails } from "./farmerDashboardService";
import "./farmer-dashboard.css";

type FarmerDashboardProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm?: SavedFarm | null;
};

export default function FarmerDashboard({
  isOpen,
  onClose,
}: FarmerDashboardProps) {
  if (!isOpen) return null;

  const feature = getFarmerDashboardDetails();

  return (
    <div
      className="rw-modal fd-modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="rw-modalbox">
        <button className="rw-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className="rw-step-label fd-badge">ROOTWISE FEATURE</div>
        <h2>{feature.name}</h2>
        <p>{feature.detail}</p>
        <button className="rw-submit" onClick={onClose}>
          Back to experience
        </button>
      </div>
    </div>
  );
}
