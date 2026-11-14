"use client";

import type { AuthMode, OnboardingStep } from "@/types/features";
import type { FarmData, FarmMapData } from "@/types/farm";
import FarmLocation from "./FarmLocation";
import FarmProfileForm from "./FarmProfileForm";

type AuthModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onboardingStep: OnboardingStep;
  authMode: AuthMode;
  setAuthMode: (mode: AuthMode) => void;
  fullName: string;
  setFullName: (name: string) => void;
  email: string;
  setEmail: (email: string) => void;
  password: string;
  setPassword: (password: string) => void;
  notice: string;
  setNotice: (notice: string) => void;
  authLoading: boolean;
  onContinueAuth: () => void;
  onConfirmLocation: (data: FarmMapData) => void;
  farm: FarmData;
  updateFarm: <K extends keyof FarmData>(key: K, value: FarmData[K]) => void;
  onRestoreSample: () => void;
  onSaveFarm: () => void;
  farmSaving: boolean;
};

export default function AuthModal({
  isOpen,
  onClose,
  onboardingStep,
  authMode,
  setAuthMode,
  fullName,
  setFullName,
  email,
  setEmail,
  password,
  setPassword,
  notice,
  setNotice,
  authLoading,
  onContinueAuth,
  onConfirmLocation,
  farm,
  updateFarm,
  onRestoreSample,
  onSaveFarm,
  farmSaving,
}: AuthModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="rw-modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="rw-modalbox">
        <button className="rw-close" onClick={onClose} aria-label="Close">
          ×
        </button>

        {onboardingStep === "auth" && (
          <>
            <div className="rw-step-label">Step 01 of 03 · Account</div>
            <h2>
              {authMode === "Login"
                ? "Welcome to ROOTWISE."
                : "Create your ROOTWISE account."}
            </h2>
            <p>Sign in or create an account before adding your farm.</p>
            <div className="rw-tabs">
              {(["Login", "Sign up"] as AuthMode[]).map((mode) => (
                <button
                  key={mode}
                  className={authMode === mode ? "active" : ""}
                  onClick={() => {
                    setAuthMode(mode);
                    setNotice("");
                  }}
                >
                  {mode}
                </button>
              ))}
            </div>
            {authMode === "Sign up" && (
              <>
                <label className="rw-label">Full name</label>
                <input
                  className="rw-field"
                  placeholder="Your name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                />
              </>
            )}
            <label className="rw-label">Email address</label>
            <input
              className="rw-field"
              type="email"
              placeholder="farmer@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <label className="rw-label">Password</label>
            <input
              className="rw-field"
              type="password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {notice && <div className="rw-notice">{notice}</div>}
            <button
              className="rw-submit"
              onClick={onContinueAuth}
              disabled={authLoading}
            >
              {authLoading
                ? "Please wait..."
                : authMode === "Sign up"
                ? "Create account →"
                : "Continue to locate your farm →"}
            </button>
            <p className="rw-helper">
              {authMode === "Sign up"
                ? "We'll send a verification link to your email before your first login."
                : "Sign in with your verified ROOTWISE account."}
            </p>
          </>
        )}

        {onboardingStep === "location" && (
          <FarmLocation onConfirmLocation={onConfirmLocation} />
        )}

        {onboardingStep === "farm" && (
          <FarmProfileForm
            farm={farm}
            updateFarm={updateFarm}
            onRestoreSample={onRestoreSample}
            onSaveFarm={onSaveFarm}
            farmSaving={farmSaving}
          />
        )}
      </div>
    </div>
  );
}
