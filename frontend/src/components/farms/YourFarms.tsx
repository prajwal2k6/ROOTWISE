"use client";

import type { SavedFarm } from "@/types/farm";
import FarmCard from "./FarmCard";

type YourFarmsProps = {
  savedFarms: SavedFarm[];
  activeFarmId: number | null;
  setActiveFarmId: (id: number) => void;
  farmsLoading: boolean;
  onOpenOnboarding: () => void;
  onStartAddingFarm: () => void;
};

export default function YourFarms({
  savedFarms,
  activeFarmId,
  setActiveFarmId,
  farmsLoading,
  onOpenOnboarding,
  onStartAddingFarm,
}: YourFarmsProps) {
  const selectedFarm = savedFarms.find((item) => item.id === activeFarmId);

  return (
    <section className="rw-your-farms" id="your-farms">
      <div className="rw-dashboard-inner">
        <div className="rw-eyebrow">YOUR ROOTWISE WORKSPACE</div>
        <h2>Your Farms</h2>
        <p className="rw-dashboard-intro">
          Save more than one farm and choose which land you want ROOTWISE to work with.
        </p>

        {farmsLoading ? (
          <p>Loading your farms...</p>
        ) : savedFarms.length === 0 ? (
          <div className="rw-empty-farms">
            <h3>No farms added yet</h3>
            <p>Sign in and add your first farm to get started.</p>
            <button className="rw-farm-cta" onClick={onOpenOnboarding}>
              Add your first farm ↗
            </button>
          </div>
        ) : (
          <div className="rw-farm-grid">
            {savedFarms.map((saved) => (
              <FarmCard
                key={saved.id}
                farm={saved}
                isSelected={activeFarmId === saved.id}
                onSelect={() => setActiveFarmId(saved.id)}
              />
            ))}
          </div>
        )}

        <button className="rw-add-farm" onClick={onStartAddingFarm}>
          ＋ Add New Farm
        </button>

        {activeFarmId !== null && selectedFarm && (
          <p className="rw-active-farm-note">
            Currently selected: <strong>{selectedFarm.farm_name}</strong>
          </p>
        )}
      </div>
    </section>
  );
}
