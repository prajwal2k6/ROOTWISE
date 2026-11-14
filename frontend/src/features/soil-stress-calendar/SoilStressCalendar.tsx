"use client";

import type { SavedFarm } from "@/types/farm";
import { getSoilStressDetails } from "./soilStressCalendarService";
import "./soil-stress-calendar.css";

type SoilStressCalendarProps = {
  isOpen: boolean;
  onClose: () => void;
  selectedFarm?: SavedFarm | null;
};

export default function SoilStressCalendar({
  isOpen,
  onClose,
}: SoilStressCalendarProps) {
  if (!isOpen) return null;

  const feature = getSoilStressDetails();

  return (
    <div
      className="rw-modal ssc-modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="rw-modalbox">
        <button className="rw-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className="rw-step-label ssc-badge">ROOTWISE FEATURE</div>
        <h2>{feature.name}</h2>
        <p>{feature.detail}</p>
        <button className="rw-submit" onClick={onClose}>
          Back to experience
        </button>
      </div>
    </div>
  );
}
