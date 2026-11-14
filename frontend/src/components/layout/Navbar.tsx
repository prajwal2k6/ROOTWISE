"use client";

import { useState } from "react";
import { featureData } from "@/types/features";

export default function Navbar() {
  const [featureMenuOpen, setFeatureMenuOpen] = useState(false);

  return (
    <nav className="rw-nav">
      <a className="rw-logo" href="#top">
        ROOT<span>WISE</span>
      </a>
      <div className="rw-navlinks">
        <a href="#farm">Your farm</a>
        <a href="#your-farms">Dashboard</a>
        <div className="rw-feature-menu-wrap">
          <button
            className={`rw-feature-menu-trigger ${featureMenuOpen ? "open" : ""}`}
            type="button"
            aria-expanded={featureMenuOpen}
            onClick={() => setFeatureMenuOpen((open) => !open)}
          >
            Features
          </button>
          {featureMenuOpen && (
            <div className="rw-feature-dropdown">
              {featureData.map((feature, index) => (
                <button
                  key={feature.number}
                  type="button"
                  onClick={() => {
                    setFeatureMenuOpen(false);
                    document
                      .getElementById(`feature-${index}`)
                      ?.scrollIntoView({ behavior: "smooth", block: "center" });
                  }}
                >
                  <span>{feature.number}</span>
                  {feature.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
