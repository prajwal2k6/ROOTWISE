"use client";

type FooterProps = {
  onOpenOnboarding: () => void;
};

export default function Footer({ onOpenOnboarding }: FooterProps) {
  return (
    <section className="rw-end">
      <div className="rw-eyebrow">ROOTWISE</div>
      <h2>Know your land. Plan your future.</h2>
      <p>
        A decision-support tool to help farmers compare options using environmental evidence
        and local knowledge—not a guarantee of crop outcomes.
      </p>
      <button className="rw-primary" onClick={onOpenOnboarding}>
        Start with your farm ↗
      </button>
    </section>
  );
}
