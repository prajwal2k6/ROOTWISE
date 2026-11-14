"use client";

type FarmIntroProps = {
  onOpenOnboarding: () => void;
};

export default function FarmIntro({ onOpenOnboarding }: FarmIntroProps) {
  return (
    <section className="rw-farm-intro" id="farm">
      <div className="rw-farm-copy">
        <div className="rw-eyebrow">Your land · Your decisions</div>
        <h2>Where is your farm?</h2>
        <p>
          Start your ROOTWISE journey. Create an account or sign in, then locate your farm
          and tell us about your crops.
        </p>
        <button className="rw-farm-cta" onClick={onOpenOnboarding}>
          Where is your farm? <span>↗</span>
        </button>
        <p className="rw-farm-note">
          First: login or sign up · Then: locate your farm · Finally: add your crop details
        </p>
      </div>
    </section>
  );
}
