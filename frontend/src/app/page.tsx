
"use client";

import { useEffect, useState } from "react";

import type { FarmData, FarmMapData, SavedFarm } from "@/types/farm";
import { emptyFarm } from "@/types/farm";

import type { AuthMode, OnboardingStep } from "@/types/features";

import { getSession, signIn, signUp } from "@/services/authService";

import Dashboard from "@/components/dashboard/Dashboard";

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

// Farm dashboard
import YourFarms from "@/components/farms/YourFarms";

// Onboarding modal
import AuthModal from "@/components/onboarding/AuthModal";

// Feature modules
import RotationMatchmaker from "@/features/rotation-matchmaker/RotationMatchmaker";
import WhatIfSimulator from "@/features/what-if-simulator/WhatIfSimulator";
import SoilStressCalendar from "@/features/soil-stress-calendar/SoilStressCalendar";
import LandMemory from "@/features/land-memory/LandMemory";
import EvidenceConfidence from "@/features/evidence-confidence/EvidenceConfidence";
import FarmerDashboard from "@/features/farmer-dashboard/FarmerDashboard";

export default function Home() {
  // --------------------------------------------------
  // AUTHENTICATION AND ONBOARDING STATE
  // --------------------------------------------------

  const [authOpen, setAuthOpen] = useState(false);

  const [authMode, setAuthMode] = useState<AuthMode>("Login");

  const [onboardingStep, setOnboardingStep] =
    useState<OnboardingStep>("auth");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  const [authLoading, setAuthLoading] = useState(false);

  // --------------------------------------------------
  // FARM LOCATION AND DETAILS
  // --------------------------------------------------

  const [location, setLocation] = useState("");
  const [locationMethod, setLocationMethod] = useState("");

  const [mapData, setMapData] = useState<FarmMapData | null>(null);

  const [farm, setFarm] = useState<FarmData>(emptyFarm);

  // --------------------------------------------------
  // FARM DATABASE STATE
  // --------------------------------------------------

  const [savedFarms, setSavedFarms] = useState<SavedFarm[]>([]);

  const [activeFarmId, setActiveFarmId] = useState<number | null>(null);

  const [farmsLoading, setFarmsLoading] = useState(false);

  const [farmSaving, setFarmSaving] = useState(false);

  // --------------------------------------------------
  // NOTIFICATIONS AND FEATURE STATE
  // --------------------------------------------------

  const [notice, setNotice] = useState("");

  const [featureOpen, setFeatureOpen] = useState<number | null>(null);

  // --------------------------------------------------
  // CLOSE MODALS WHEN ESCAPE IS PRESSED
  // --------------------------------------------------

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setAuthOpen(false);
        setFeatureOpen(null);
      }
    };

    window.addEventListener("keydown", onKey);

    return () => {
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  // --------------------------------------------------
  // LOAD USER'S FARMS WHEN A SESSION EXISTS
  // --------------------------------------------------

  useEffect(() => {
    async function initializeFarms() {
      try {
        const session = await getSession();

        if (session) {
          await loadMyFarms();
        }
      } catch (error) {
        console.error("Unable to initialize farms:", error);
      }
    }

    initializeFarms();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --------------------------------------------------
  // UPDATE FARM FORM FIELDS
  // --------------------------------------------------

  function updateFarm<K extends keyof FarmData>(
    key: K,
    value: FarmData[K]
  ) {
    setFarm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  // --------------------------------------------------
  // LOAD FARMS BELONGING TO THE LOGGED-IN USER
  // --------------------------------------------------

  async function loadMyFarms(): Promise<SavedFarm[]> {
    const session = await getSession();

    if (!session) {
      setSavedFarms([]);
      setActiveFarmId(null);
      return [];
    }

    setFarmsLoading(true);

    try {
      const rows = await fetchMyFarms(session.access_token);

      setSavedFarms(rows);

      setActiveFarmId((current) => {
        // Keep the current selection if it still exists.
        if (current !== null && rows.some((farm) => farm.id === current)) {
          return current;
        }

        // Otherwise select the most recently saved farm.
        return rows[0]?.id ?? null;
      });

      return rows;
    } finally {
      setFarmsLoading(false);
    }
  }

  // --------------------------------------------------
  // RESET FARM FORM FOR A NEW FARM
  // --------------------------------------------------

  function resetFarmForm() {
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
  }

  // --------------------------------------------------
  // START ADDING A NEW FARM
  // --------------------------------------------------

  async function startAddingFarm() {
    try {
      const session = await getSession();

      if (!session) {
        openOnboarding();
        return;
      }

      resetFarmForm();

      setOnboardingStep("location");
      setAuthOpen(true);
    } catch (error) {
      console.error("Unable to check login session:", error);
      setNotice("Unable to verify your login. Please try again.");
    }
  }

  // --------------------------------------------------
  // LOGIN AND SIGNUP
  // --------------------------------------------------

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
        const { error } = await signUp(
          email,
          password,
          fullName
        );

        if (error) {
          throw error;
        }
      } else {
        const { error } = await signIn(email, password);

        if (error) {
          throw error;
        }
      }

      setNotice("");

      // Load existing farms after successful authentication.
      const existingFarms = await loadMyFarms();

      if (authMode === "Login" && existingFarms.length > 0) {
        setAuthOpen(false);

        setTimeout(() => {
          document
            .getElementById("your-farms")
            ?.scrollIntoView({ behavior: "smooth" });
        }, 100);
      } else {
        // New user or user without saved farms.
        resetFarmForm();

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

  // --------------------------------------------------
  // SAVE FARM TO BACKEND DATABASE
  // --------------------------------------------------

  async function saveFarmDetails() {
    setNotice("");

    if (!mapData) {
      setNotice("Please select and confirm the farm location first.");
      return;
    }

    if (!mapData.boundary || mapData.boundary.length < 3) {
      setNotice("Please draw a valid farm boundary on the map.");
      return;
    }

    if (!farm.farmName.trim()) {
      setNotice("Please enter a farm name.");
      return;
    }

    setFarmSaving(true);

    try {
      // Get the currently authenticated user.
      const session = await getSession();

      if (!session?.access_token) {
        throw new Error(
          "Your session has expired. Please log in again."
        );
      }

      // Build the backend payload from the farm form and map data.
      const payload = buildFarmPayload(farm, mapData);

      // Save the farm using the authenticated API request.
      const result = await createFarm(
        payload,
        session.access_token
      );

      // Refresh the saved farms list.
      const updatedFarms = await fetchMyFarms(session.access_token);

      setSavedFarms(updatedFarms);

      // Automatically select the newly created farm.
      setActiveFarmId(result.id);

      // Close onboarding after successful save.
      setAuthOpen(false);

      setOnboardingStep("auth");

      setNotice("");

      // Scroll to the user's saved farms.
      setTimeout(() => {
        document
          .getElementById("your-farms")
          ?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to save this farm. Please try again.";

      setNotice(message);
    } finally {
      setFarmSaving(false);
    }
  }

  // --------------------------------------------------
  // OPEN ONBOARDING MODAL
  // --------------------------------------------------

  function openOnboarding() {
    setAuthMode("Login");
    setOnboardingStep("auth");
    setNotice("");
    setAuthOpen(true);
  }

  // --------------------------------------------------
  // CURRENTLY SELECTED FARM
  // --------------------------------------------------

  const selectedFarm =
    savedFarms.find((item) => item.id === activeFarmId) ?? null;

  // --------------------------------------------------
  // PAGE UI
  // --------------------------------------------------

  return (
    <main className="rw-root">

      {/* NAVIGATION */}
      <Navbar />

      {/* HERO SECTION */}
      <div className="rw-opening" id="top">
        <video
          className="rw-video"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        >
          <source
            src="/videos/rootwise-background.mp4"
            type="video/mp4"
          />
        </video>

        <Hero />

        <FarmIntro onOpenOnboarding={openOnboarding} />
      </div>

      {/* USER'S SAVED FARMS */}
      <YourFarms
        savedFarms={savedFarms}
        activeFarmId={activeFarmId}
        setActiveFarmId={setActiveFarmId}
        farmsLoading={farmsLoading}
        onOpenOnboarding={openOnboarding}
        onStartAddingFarm={startAddingFarm}
      />

      {/* SIX FEATURE MODULES */}
      <FeatureShowcase
        onOpenFeature={(index) => setFeatureOpen(index)}
      />

      {/* FOOTER */}
      <Footer onOpenOnboarding={openOnboarding} />

      {/* LOGIN, LOCATION AND FARM DETAILS MODAL */}
      <AuthModal
        isOpen={authOpen}
        onClose={() => {
          if (!authLoading && !farmSaving) {
            setAuthOpen(false);
          }
        }}
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

        // Called after the user confirms the map location.
        onConfirmLocation={(data) => {
          setMapData(data);

          const locationText =
            `${data.latitude.toFixed(6)}, ${data.longitude.toFixed(6)}`;

          setLocation(locationText);

          setLocationMethod("MapLibre satellite map");

          // Store the mapped area in the form.
          setFarm((current) => ({
            ...current,
            location: locationText,
            locationMethod: "MapLibre satellite map",
            acres: data.areaAcres.toFixed(3),
          }));

          setNotice("");

          // Move to the farm details step.
          setOnboardingStep("farm");
        }}

        farm={farm}
        updateFarm={updateFarm}

        // Restore the sample farm values.
        onRestoreSample={() => {
          setFarm({
            ...emptyFarm,
            location,
            locationMethod,
          });
        }}

        onSaveFarm={saveFarmDetails}
        farmSaving={farmSaving}
      />

      {/* ------------------------------------------------
          FEATURE 01: ROTATION MATCHMAKER
      ------------------------------------------------ */}

      <RotationMatchmaker
        isOpen={featureOpen === 0}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
        onGoToFarms={() => {
          setFeatureOpen(null);

          document
            .getElementById("your-farms")
            ?.scrollIntoView({ behavior: "smooth" });
        }}
      />

      {/* ------------------------------------------------
          FEATURE 02: WHAT-IF SIMULATOR
      ------------------------------------------------ */}

      <WhatIfSimulator
        isOpen={featureOpen === 1}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
        onGoToFarms={() => {
          setFeatureOpen(null);

          document
            .getElementById("your-farms")
            ?.scrollIntoView({ behavior: "smooth" });
        }}
      />

      {/* ------------------------------------------------
          FEATURE 03: SOIL STRESS CALENDAR
      ------------------------------------------------ */}

      <SoilStressCalendar
        isOpen={featureOpen === 2}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />

      {/* ------------------------------------------------
          FEATURE 04: LAND MEMORY
      ------------------------------------------------ */}

      <LandMemory
        isOpen={featureOpen === 3}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />

      {/* ------------------------------------------------
          FEATURE 05: EVIDENCE AND CONFIDENCE
      ------------------------------------------------ */}

      <EvidenceConfidence
        isOpen={featureOpen === 4}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />

      {/* ------------------------------------------------
          FEATURE 06: FARMER DASHBOARD
      ------------------------------------------------ */}

      <FarmerDashboard
        isOpen={featureOpen === 5}
        onClose={() => setFeatureOpen(null)}
        selectedFarm={selectedFarm}
      />

    </main>
  );
}
