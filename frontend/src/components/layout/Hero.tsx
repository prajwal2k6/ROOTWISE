"use client";

export default function Hero() {
  return (
    <section className="rw-hero">
      <div className="rw-hero-copy">
        <div className="rw-eyebrow">Earth intelligence · Better crop decisions</div>
        <h1>
          ROOT<span>WISE</span>
        </h1>
        <p>
          Know your land. Plan your future. Bring satellite observations and local farm
          knowledge together to explore smarter crop-rotation choices.
        </p>
        <button
          className="rw-primary"
          onClick={() =>
            document.getElementById("farm")?.scrollIntoView({ behavior: "smooth" })
          }
        >
          Begin your journey <span>↘</span>
        </button>
      </div>
      <div className="rw-scroll">↓ &nbsp; Scroll to discover</div>
    </section>
  );
}
