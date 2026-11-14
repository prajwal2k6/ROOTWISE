"use client";

import { useEffect, useRef, useState } from "react";
import { featureData } from "@/types/features";

type FeatureShowcaseProps = {
  onOpenFeature: (index: number) => void;
};

export default function FeatureShowcase({ onOpenFeature }: FeatureShowcaseProps) {
  const [activeFeature, setActiveFeature] = useState(0);
  const featureRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    featureRefs.current.forEach((node, index) => {
      if (!node) return;
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) setActiveFeature(index);
        },
        { threshold: 0.48 }
      );
      observer.observe(node);
      observers.push(observer);
    });
    return () => observers.forEach((observer) => observer.disconnect());
  }, []);

  return (
    <>
      <section className="rw-features" id="features">
        <div className="rw-scene">
          {featureData.map((feature, index) => (
            <img
              key={feature.number}
              className={`rw-scene-img ${activeFeature === index ? "active" : ""}`}
              src={feature.image}
              alt="Agricultural landscape"
            />
          ))}
          <div className={`rw-scene-heading ${activeFeature % 2 ? "side-right" : ""}`}>
            <div className="rw-eyebrow">ROOTWISE INTELLIGENCE</div>
            <h2>{featureData[activeFeature].title}</h2>
            <p>{featureData[activeFeature].description}</p>
          </div>
        </div>
        <div className="rw-feature-track">
          {featureData.map((feature, index) => (
            <div
              id={`feature-${index}`}
              className={`rw-feature-step ${index % 2 ? "card-left" : ""}`}
              key={feature.number}
              ref={(node) => {
                featureRefs.current[index] = node;
              }}
            >
              <article
                className={`rw-feature-card ${activeFeature === index ? "visible" : ""}`}
              >
                <div className="rw-feature-num">
                  {feature.number} / {feature.name}
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
                <button onClick={() => onOpenFeature(index)}>{feature.action} ↗</button>
              </article>
            </div>
          ))}
        </div>
      </section>

      <div className="rw-dots">
        {featureData.map((feature, index) => (
          <button
            aria-label={`Go to ${feature.name}`}
            key={feature.number}
            className={`rw-dot ${activeFeature === index ? "active" : ""}`}
            onClick={() =>
              featureRefs.current[index]?.scrollIntoView({
                behavior: "smooth",
                block: "center",
              })
            }
          />
        ))}
      </div>
    </>
  );
}
