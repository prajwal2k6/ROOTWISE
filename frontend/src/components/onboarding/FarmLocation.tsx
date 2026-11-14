"use client";

import FarmMap, { type FarmMapData } from "@/components/FarmMap";

type FarmLocationProps = {
  onConfirmLocation: (data: FarmMapData) => void;
};

export default function FarmLocation({ onConfirmLocation }: FarmLocationProps) {
  return (
    <>
      <div className="rw-step-label">Step 02 of 03 · Farm location</div>
      <h2>Locate your farm.</h2>
      <p>
        Search for your village or district, select your farm location, and draw its
        boundary on the satellite map.
      </p>
      <FarmMap onSave={onConfirmLocation} />
      <p className="rw-helper">
        The outlined area is an approximate map-based measurement. Check the boundary and
        area before continuing.
      </p>
    </>
  );
}
