"use client";

import { useState } from "react";
import Link from "next/link";
import { featureData } from "@/types/features";

export default function Navbar() {
  const [featureMenuOpen, setFeatureMenuOpen] = useState(false);

  return (
    <nav className="rw-nav">
      <Link className="rw-logo" href="/">
        ROOT<span>WISE</span>
      </Link>

      <div className="rw-navlinks">
        <Link href="/#farm">Your farm</Link>
        <Link href="/dashboard">Dashboard</Link>

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
                    window.location.href = `/#feature-${index}`;
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
