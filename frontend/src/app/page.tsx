"use client";

import { useEffect, useState } from "react";
import type { FarmData, FarmMapData, SavedFarm } from "@/types/farm";
import { emptyFarm } from "@/types/farm";
import type { AuthMode, OnboardingStep } from "@/types/features";
import { getSession, signIn, signUp } from "@/services/authService";
import {
  buildFarmPayload,
  createFarm,
  fetchMyFarms,
} from "@/services/farmService";

// Layout components
import Navbar from "@/components/layout/Navbar";
import Hero from "@/components/layout/Hero";
import FarmIntro from "@/components/layout/FarmIntro";
import FeatureShowcase from "@/components/layout/FeatureShowcase";
import Footer from "@/components/layout/Footer";

// Farm dashboard component
import YourFarms from "@/components/farms/YourFarms";

// Onboarding modal component
import AuthModal from "@/components/onboarding/AuthModal";

// Six feature modules
import RotationMatchmaker from "@/features/rotation-matchmaker/RotationMatchmaker";
import WhatIfSimulator from "@/features/what-if-simulator/WhatIfSimulator";
import SoilStressCalendar from "@/features/soil-stress-calendar/SoilStressCalendar";
import LandMemory from "@/features/land-memory/LandMemory";
import EvidenceConfidence from "@/features/evidence-confidence/EvidenceConfidence";
import FarmerDashboard from "@/features/farmer-dashboard/FarmerDashboard";

export default function Home() {
  const [authOpen, setAuthOpen] = useState(false);
  const [featureOpen, setFeatureOpen] = useState<number | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("Login");
  const [onboardingStep, setOnboardingStep] = useState<OnboardingStep>("auth");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [location, setLocation] = useState("");
  const [locationMethod, setLocationMethod] = useState("");
  const [mapData, setMapData] = useState<FarmMapData | null>(null);
  const [farm, setFarm] = useState<FarmData>(emptyFarm);
  const [notice, setNotice] = useState("");
  const [savedFarms, setSavedFarms] = useState<SavedFarm[]>([]);
  const [activeFarmId, setActiveFarmId] = useState<number | null>(null);
  const [farmsLoading, setFarmsLoading] = useState(false);
  const [farmSaving, setFarmSaving] = useState(false);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setAuthOpen(false);
        setFeatureOpen(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    getSession().then((session) => {
      if (session) {
        loadMyFarms().catch((error) =>
          console.error("Unable to load farms:", error)
        );
      }
    });
  }, []);

  function updateFarm<K extends keyof FarmData>(key: K, value: FarmData[K]) {
    setFarm((current) => ({ ...current, [key]: value }));
  }

  async function loadMyFarms() {
    const session = await getSession();
    if (!session) return [] as SavedFarm[];
    setFarmsLoading(true);
    try {
      const rows = await fetchMyFarms(session.access_token);
      setSavedFarms(rows);
      setActiveFarmId((current) => current ?? rows[0]?.id ?? null);
      return rows;
    } finally {
      setFarmsLoading(false);
    }
  }

  async function startAddingFarm() {
    const session = await getSession();
    if (!session) {
      openOnboarding();
      return;
    }
    setFarm({
      ...emptyFarm,
      farmName: "",
      acres: "",
      soil: "Not sure",
      irrigation: "Not sure",
      mainCrop: "",
      otherCrops: "",
      sowing: "Not sure",
      harvest: "Not sure",
      sequence: "",
      frequency: "Not sure",
      priority: "Not sure",
      notes: "",
      location: "",
      locationMethod: "",
    });
    setMapData(null);
    setLocation("");
    setLocationMethod("");
    setNotice("");
    setOnboardingStep("location");
    setAuthOpen(true);
  }

  async function continueAuth() {
    setNotice("");

    if (!email.trim() || !password.trim()) {
      setNotice("Enter an email address and password to continue.");
      return;
    }

    if (password.length < 8) {
      setNotice("Your password must contain at least 8 characters.");
      return;
    }

    if (authMode === "Sign up" && !fullName.trim()) {
      setNotice("Please enter your full name.");
      return;
    }

    setAuthLoading(true);

    try {
      if (authMode === "Sign up") {
        const { data, error } = await signUp(email, password, fullName);

        if (error) throw error;

        // With email confirmation enabled, Supabase creates the account
        // but does not create a session until the farmer verifies their email.
        if (!data.session) {
          setNotice(
            "Account created! Check your email and click the verification link. After verifying, return here and log in."
          );
          setAuthMode("Login");
          setPassword("");
          return;
        }
      } else {
        const { error } = await signIn(email, password);

        if (error) throw error;
      }

      setNotice("");
      const existingFarms = await loadMyFarms();
      if (authMode === "Login" && existingFarms.length > 0) {
        setAuthOpen(false);
        document
          .getElementById("your-farms")
          ?.scrollIntoView({ behavior: "smooth" });
      } else {
        setFarm({
          ...emptyFarm,
          farmName: "",
          acres: "",
          soil: "Not sure",
          irrigation: "Not sure",
          mainCrop: "",
          otherCrops: "",
          sowing: "Not sure",
          harvest: "Not sure",
          sequence: "",
          frequency: "Not sure",
          priority: "Not sure",
          notes: "",
          location: "",
          locationMethod: "",
        });
        setMapData(null);
        setOnboardingStep("location");
      }
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Authentication failed. Please try again.";
      setNotice(message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function saveFarmDetails() {
    setNotice("");
    if (!mapData) {
      setNotice("Please select and confirm the farm location first.");
      return;
    }
    if (!farm.farmName.trim()) {
      setNotice("Please enter a farm name.");
      return;
    }
    const session = await getSession();
    if (!session) {
      setNotice("Your session has expired. Please log in again.");
      return;
    }

    setFarmSaving(true);
    try {
      const payload = buildFarmPayload(farm, mapData);
      const result = await createFarm(payload, session.access_token);
      await loadMyFarms();
      setActiveFarmId(result.id);
      setAuthOpen(false);
      setNotice("");
      setOnboardingStep("auth");
      setTimeout(
        () =>
          document
            .getElementById("your-farms")
            ?.scrollIntoView({ behavior: "smooth" }),
        100
      );
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Unable to save this farm. Please try again."
      );
    } finally {
      setFarmSaving(false);
    }
  }

  function openOnboarding() {
    setAuthMode("Login");
    setOnboardingStep("auth");
    setNotice("");
    setAuthOpen(true);
  }

  const selectedFarm =
    savedFarms.find((item) => item.id === activeFarmId) ?? null;

  return (
    <main className="rw-root">
      <Navbar />

      <div className="rw-opening" id="top">
        <video
          className="rw-video"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        >
          <source src="/videos/rootwise-background.mp4" type="video/mp4" />
        </video>
        <Hero />
        <FarmIntro onOpenOnboarding={openOnboarding} />
      </div>

      <YourFarms
        savedFarms={savedFarms}
        activeFarmId={activeFarmId}
        setActiveFarmId={setActiveFarmId}
        farmsLoading={farmsLoading}
        onOpenOnboarding={openOnboarding}
        onStartAddingFarm={startAddingFarm}
      />

      <FeatureShowcase onOpenFeature={(index) => setFeatureOpen(index)} />

      <Footer onOpenOnboarding={openOnboarding} />

      <AuthModal
        isOpen={authOpen}
        onClose={() => setAuthOpen(false)}
        onboardingStep={onboardingStep}
        authMode={authMode}
        setAuthMode={setAuthMode}
        fullName={fullName}
        setFullName={setFullName}
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        notice={notice}
        setNotice={setNotice}
        authLoading={authLoading}
        onContinueAuth={continueAuth}
        onConfirmLocation={(data) => {
          setMapData(data);
          const locationText = `${data.latitude.toFixed(6)}, ${data.longitude.toFixed(6)}`;
          setLocation(locationText);
          setLocationMethod("MapLibre satellite map");
          setFarm((current) => ({
            ...current,
            location: locationText,
            locationMethod: "MapLibre satellite map",
            acres: data.areaAcres.toFixed(3),
          }));
          setNotice("");
          setOnboardingStep("farm");
        }}
        farm={farm}
        updateFarm={updateFarm}
        onRestoreSample={() => setFarm({ ...emptyFarm, location, locationMethod })}
        onSaveFarm={saveFarmDetails}
        farmSaving={farmSaving}
      />

      <RotationMatchmaker
        isOpen={featureOpen === 0}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
        onGoToFarms={() =>
          document
            .getElementById("your-farms")
            ?.scrollIntoView({ behavior: "smooth" })
        }
      />

      <WhatIfSimulator
        isOpen={featureOpen === 1}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
        onGoToFarms={() =>
          document
            .getElementById("your-farms")
            ?.scrollIntoView({ behavior: "smooth" })
        }
      />

      <SoilStressCalendar
        isOpen={featureOpen === 2}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />

      <LandMemory
        isOpen={featureOpen === 3}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />

      <EvidenceConfidence
        isOpen={featureOpen === 4}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />

      <FarmerDashboard
        isOpen={featureOpen === 5}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />
    </main>
  );
}
