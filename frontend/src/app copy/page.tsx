"use client";

import { useEffect, useRef, useState } from "react";
import { supabase } from "@/lib/supabase";

type AuthMode = "Login" | "Sign up";
type FarmData = {
  farmName: string; acres: string; soil: string; irrigation: string;
  mainCrop: string; otherCrops: string; sowing: string; harvest: string;
  sequence: string; frequency: string; priority: string; notes: string;
  location: string; locationMethod: string;
};

const featureData = [
  {
    number: "01", name: "ROTATION MATCHMAKER", title: "Compare your next move.",
    description: "Weigh your current crop sequence against soil-restoration and climate-resilience rotations, with the trade-offs made clear.",
    detail: "Compare crop-sequence strategies, including benefits, risks, trade-offs and configurable scoring assumptions.",
    image: "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=2200&q=85",
    action: "Explore rotations",
  },
  {
    number: "02", name: "WHAT-IF SIMULATOR", title: "What if the season changes?",
    description: "Adjust rainfall or temperature assumptions and explore how different conditions could change the relative suitability of crop rotations.",
    detail: "Try user-defined scenarios, such as lower rainfall or higher average temperature. These are scenarios, not forecasts.",
    image: "https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=2200&q=85",
    action: "Try simulator",
  },
  {
    number: "03", name: "SOIL STRESS CALENDAR", title: "Know when your land needs attention.",
    description: "Spot seasonal windows that may bring low soil moisture, high temperatures or irregular rainfall—before planning your next crop.",
    detail: "Explore potentially vulnerable periods by season or month, using available environmental indicators.",
    image: "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=2200&q=85",
    action: "Explore calendar",
  },
  {
    number: "04", name: "LAND MEMORY", title: "Every field has a story.",
    description: "Explore historical rainfall, temperature, soil-moisture and vegetation patterns around your selected farm.",
    detail: "Review environmental patterns over time and understand what available observations can—and cannot—tell you.",
    image: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=2200&q=85",
    action: "Explore Land Memory",
  },
  {
    number: "05", name: "EVIDENCE & CONFIDENCE", title: "Understand the evidence.",
    description: "See which observations and farm details support each insight, along with uncertainty, limitations and missing data.",
    detail: "Review observations and local inputs behind each comparison, including data gaps and confidence limitations.",
    image:"/images/evidence-confidence.png",
    action: "Explore evidence",
  },
  {
    number: "06", name: "FARMER DASHBOARD", title: "Your farm, in one clear view.",
    description: "Bring together your farm profile, environmental indicators, seasonal stress and crop-rotation comparisons in one place.",
    detail: "A central workspace for farm details, available environmental indicators, maps and crop-rotation comparisons.",
    image: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=2200&q=85",
    action: "Open dashboard",
  }
];

const emptyFarm: FarmData = {
  farmName: "Green Valley Farm", acres: "5", soil: "Red loamy soil",
  irrigation: "Borewell", mainCrop: "Ragi (finger millet)",
  otherCrops: "Maize, tomato, groundnut", sowing: "Kharif (June–July)",
  harvest: "October–December", sequence: "Ragi → Groundnut → Maize",
  frequency: "Twice a year", priority: "Save water and manage dry periods",
  notes: "Water availability is lower during March and April.",
  location: "", locationMethod: "",
};

export default function Home() {
  const [authOpen, setAuthOpen] = useState(false);
  const [featureOpen, setFeatureOpen] = useState<number | null>(null);
  const [featureMenuOpen, setFeatureMenuOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("Login");
  const [onboardingStep, setOnboardingStep] = useState<"auth" | "location" | "farm">("auth");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [location, setLocation] = useState("");
  const [locationMethod, setLocationMethod] = useState("");
  const [farm, setFarm] = useState<FarmData>(emptyFarm);
  const [activeFeature, setActiveFeature] = useState(0);
  const [notice, setNotice] = useState("");
  const featureRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    featureRefs.current.forEach((node, index) => {
      if (!node) return;
      const observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) setActiveFeature(index);
      }, { threshold: 0.48 });
      observer.observe(node);
      observers.push(observer);
    });
    return () => observers.forEach((observer) => observer.disconnect());
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setAuthOpen(false); setFeatureOpen(null); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function updateFarm<K extends keyof FarmData>(key: K, value: FarmData[K]) {
    setFarm((current) => ({ ...current, [key]: value }));
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
        const { data, error } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: {
            data: { full_name: fullName.trim() },
            emailRedirectTo: `${window.location.origin}/`,
          },
        });

        if (error) throw error;

        // With email confirmation enabled, Supabase creates the account
        // but does not create a session until the farmer verifies their email.
        if (!data.session) {
          setNotice("Account created! Check your email and click the verification link. After verifying, return here and log in.");
          setAuthMode("Login");
          setPassword("");
          return;
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });

        if (error) throw error;
      }

      setNotice("");
      setOnboardingStep("location");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Authentication failed. Please try again.";
      setNotice(message);
    } finally {
      setAuthLoading(false);
    }
  }

  function chooseLocation(method: string, value: string) {
    setLocationMethod(method);
    setLocation(value);
    setFarm((current) => ({ ...current, location: value, locationMethod: method }));
    setOnboardingStep("farm");
  }

  function saveFarm() {
    const data = { ...farm, location, locationMethod };
    localStorage.setItem("rootwiseDemoFarm", JSON.stringify(data));
    setAuthOpen(false);
    setNotice("");
    document.getElementById("features")?.scrollIntoView({ behavior: "smooth" });
  }

  function openOnboarding() {
    setAuthMode("Login");
    setOnboardingStep("auth");
    setNotice("");
    setAuthOpen(true);
  }

  return (
    <main className="rw-root">
      <nav className="rw-nav">
        <a className="rw-logo" href="#top">ROOT<span>WISE</span></a>
        <div className="rw-navlinks">
          <a href="#farm">Your farm</a>
          <a href="#feature-5">Dashboard</a>
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
                      document.getElementById(`feature-${index}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
                    }}
                  >
                    <span>{feature.number}</span>{feature.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </nav>

      <div className="rw-opening" id="top">
        <video className="rw-video" autoPlay muted loop playsInline preload="auto">
          <source src="/videos/rootwise-background.mp4" type="video/mp4" />
        </video>
        <section className="rw-hero">
          <div className="rw-hero-copy">
            <div className="rw-eyebrow">Earth intelligence · Better crop decisions</div>
            <h1>ROOT<span>WISE</span></h1>
            <p>Know your land. Plan your future. Bring satellite observations and local farm knowledge together to explore smarter crop-rotation choices.</p>
            <button className="rw-primary" onClick={() => document.getElementById("farm")?.scrollIntoView({ behavior: "smooth" })}>Begin your journey <span>↘</span></button>
          </div>
          <div className="rw-scroll">↓ &nbsp; Scroll to discover</div>
        </section>
        <section className="rw-farm-intro" id="farm">
          <div className="rw-farm-copy">
            <div className="rw-eyebrow">Your land · Your decisions</div>
            <h2>Where is your farm?</h2>
            <p>Start your ROOTWISE journey. Create an account or sign in, then locate your farm and tell us about your crops.</p>
            <button className="rw-farm-cta" onClick={openOnboarding}>Where is your farm? <span>↗</span></button>
            <p className="rw-farm-note">First: login or sign up · Then: locate your farm · Finally: add your crop details</p>
          </div>
        </section>
      </div>

      <section className="rw-features" id="features">
        <div className="rw-scene">
          {featureData.map((feature, index) => (
            <img key={feature.number} className={`rw-scene-img ${activeFeature === index ? "active" : ""}`} src={feature.image} alt="Agricultural landscape" />
          ))}
          <div className={`rw-scene-heading ${activeFeature % 2 ? "side-right" : ""}`}>
            <div className="rw-eyebrow">ROOTWISE INTELLIGENCE</div>
            <h2>{featureData[activeFeature].title}</h2>
            <p>{featureData[activeFeature].description}</p>
          </div>
        </div>
        <div className="rw-feature-track">
          {featureData.map((feature, index) => (
            <div id={`feature-${index}`} className={`rw-feature-step ${index % 2 ? "card-left" : ""}`} key={feature.number} ref={(node) => { featureRefs.current[index] = node; }}>
              <article className={`rw-feature-card ${activeFeature === index ? "visible" : ""}`}>
                <div className="rw-feature-num">{feature.number} / {feature.name}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
                <button onClick={() => setFeatureOpen(index)}>{feature.action} ↗</button>
              </article>
            </div>
          ))}
        </div>
      </section>

      <section className="rw-end">
        <div className="rw-eyebrow">ROOTWISE</div>
        <h2>Know your land. Plan your future.</h2>
        <p>A decision-support tool to help farmers compare options using environmental evidence and local knowledge—not a guarantee of crop outcomes.</p>
        <button className="rw-primary" onClick={openOnboarding}>Start with your farm ↗</button>
      </section>

      <div className="rw-dots">
        {featureData.map((feature, index) => (
          <button aria-label={`Go to ${feature.name}`} key={feature.number} className={`rw-dot ${activeFeature === index ? "active" : ""}`} onClick={() => featureRefs.current[index]?.scrollIntoView({ behavior: "smooth", block: "center" })} />
        ))}
      </div>

      {authOpen && (
        <div className="rw-modal" onMouseDown={(event) => { if (event.target === event.currentTarget) setAuthOpen(false); }}>
          <div className="rw-modalbox">
            <button className="rw-close" onClick={() => setAuthOpen(false)} aria-label="Close">×</button>
            {onboardingStep === "auth" && <>
              <div className="rw-step-label">Step 01 of 03 · Account</div>
              <h2>{authMode === "Login" ? "Welcome to ROOTWISE." : "Create your ROOTWISE account."}</h2>
              <p>Sign in or create an account before adding your farm.</p>
              <div className="rw-tabs">
                {(["Login", "Sign up"] as AuthMode[]).map((mode) => <button key={mode} className={authMode === mode ? "active" : ""} onClick={() => { setAuthMode(mode); setNotice(""); }}>{mode}</button>)}
              </div>
              {authMode === "Sign up" && <><label className="rw-label">Full name</label><input className="rw-field" placeholder="Your name" value={fullName} onChange={(event) => setFullName(event.target.value)} /></>}
              <label className="rw-label">Email address</label>
              <input className="rw-field" type="email" placeholder="farmer@example.com" value={email} onChange={(event) => setEmail(event.target.value)} />
              <label className="rw-label">Password</label>
              <input className="rw-field" type="password" placeholder="At least 8 characters" value={password} onChange={(event) => setPassword(event.target.value)} />
              {notice && <div className="rw-notice">{notice}</div>}
              <button className="rw-submit" onClick={continueAuth} disabled={authLoading}>
                {authLoading ? "Please wait..." : authMode === "Sign up" ? "Create account →" : "Continue to locate your farm →"}
              </button>
              <p className="rw-helper">{authMode === "Sign up" ? "We'll send a verification link to your email before your first login." : "Sign in with your verified ROOTWISE account."}</p>
            </>}

            {onboardingStep === "location" && <>
              <div className="rw-step-label">Step 02 of 03 · Farm location</div>
              <h2>Locate your farm.</h2>
              <p>Choose one of these three ways to identify your farm location.</p>
              <div className="rw-choice-grid">
                <button className="rw-choice" onClick={() => chooseLocation("Current location", "Device location (demo)")}><span>⌖</span><strong>Current location</strong><small>Use device GPS</small></button>
                <button className="rw-choice" onClick={() => chooseLocation("Locate on map", "Pinned farm location (demo)")}><span>▧</span><strong>Locate on map</strong><small>Choose a map pin</small></button>
                <button className="rw-choice" onClick={() => setLocationMethod("Enter address")}><span>⌕</span><strong>Enter address</strong><small>Type farm address</small></button>
              </div>
              {locationMethod === "Enter address" && <>
                <label className="rw-label">Farm address / village / district</label>
                <input className="rw-field" placeholder="e.g. Doddaballapur, Bengaluru Rural, Karnataka" value={location} onChange={(event) => setLocation(event.target.value)} />
                <button className="rw-submit" onClick={() => { if (!location.trim()) { setNotice("Please enter your farm address."); return; } chooseLocation("Entered address", location); }}>Use this address →</button>
              </>}
              <p className="rw-helper">Location actions are simulated in this front-end demo. A real build will request GPS permission and use a map/geocoding service.</p>
            </>}

            {onboardingStep === "farm" && <>
              <div className="rw-step-label">Step 03 of 03 · Farm profile</div>
              <h2>Tell us about your farm.</h2>
              <p>Add a few details so ROOTWISE can organise the right environmental indicators and compare crop rotations. You can edit these sample values.</p>
              <div className="rw-sample-note">Sample data is prefilled. Replace it with your farm&apos;s actual details.</div>
              <div className="rw-form-grid">
                <Field label="Farm name" value={farm.farmName} onChange={(v) => updateFarm("farmName", v)} />
                <Field label="Farm size (acres)" value={farm.acres} onChange={(v) => updateFarm("acres", v)} type="number" />
                <SelectField label="Soil type" value={farm.soil} onChange={(v) => updateFarm("soil", v)} options={["Red loamy soil", "Black cotton soil", "Sandy soil", "Clay soil", "Alluvial soil", "Not sure"]} />
                <SelectField label="Irrigation access" value={farm.irrigation} onChange={(v) => updateFarm("irrigation", v)} options={["Borewell", "Rain-fed", "Canal / river", "Drip irrigation", "Multiple sources", "Not sure"]} />
                <Field label="Main crop grown" value={farm.mainCrop} onChange={(v) => updateFarm("mainCrop", v)} />
                <Field label="Other crops grown" value={farm.otherCrops} onChange={(v) => updateFarm("otherCrops", v)} />
                <SelectField label="Usual sowing season / month" value={farm.sowing} onChange={(v) => updateFarm("sowing", v)} options={["Kharif (June–July)", "Rabi (October–November)", "Summer (February–March)", "Multiple seasons", "Varies each year", "Not sure"]} />
                <SelectField label="Typical harvest period" value={farm.harvest} onChange={(v) => updateFarm("harvest", v)} options={["September–October", "November–December", "January–March", "April–May", "Different times each year", "Not sure"]} />
                <Field label="Previous crop sequence" value={farm.sequence} onChange={(v) => updateFarm("sequence", v)} />
                <SelectField label="How often do you grow crops?" value={farm.frequency} onChange={(v) => updateFarm("frequency", v)} options={["Once a year", "Twice a year", "Three or more times a year", "Depends on rainfall and water", "Not sure"]} />
              </div>
              <label className="rw-label">What would you most like help with?</label>
              <SelectField label="" value={farm.priority} onChange={(v) => updateFarm("priority", v)} options={["Save water and manage dry periods", "Improve soil health", "Improve climate resilience", "Balance multiple priorities", "Improve crop productivity", "Not sure"]} />
              <label className="rw-label">Previous crops grown (optional)</label>
              <textarea className="rw-field" rows={2} value={farm.notes} onChange={(event) => updateFarm("notes", event.target.value)} placeholder="e.g. Ragi → Groundnut → Maize" />
              <div className="rw-form-actions">
                <button className="rw-secondary" onClick={() => setFarm({ ...emptyFarm, location, locationMethod })}>↻ Restore sample data</button>
                <button className="rw-submit" onClick={saveFarm}>Save farm details & explore features →</button>
              </div>
              <p className="rw-helper">Sample values are fictional examples for testing. Replace them with accurate farm information before using real analysis.</p>
            </>}
          </div>
        </div>
      )}

      {featureOpen !== null && (
        <div className="rw-modal" onMouseDown={(event) => { if (event.target === event.currentTarget) setFeatureOpen(null); }}>
          <div className="rw-modalbox">
            <button className="rw-close" onClick={() => setFeatureOpen(null)} aria-label="Close">×</button>
            <div className="rw-step-label">ROOTWISE FEATURE</div>
            <h2>{featureData[featureOpen].name}</h2>
            <p>{featureData[featureOpen].detail}</p>
            <button className="rw-submit" onClick={() => setFeatureOpen(null)}>Back to experience</button>
          </div>
        </div>
      )}

      <style jsx global>{`
        :root{--rw-leaf:#c6dfa9;--rw-cream:#f4f3e9;--rw-ink:#183629;--rw-forest:#123827}
        *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--rw-cream);color:var(--rw-ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
        .rw-root{overflow:clip;background:var(--rw-cream)}.rw-nav{position:fixed;z-index:30;top:0;left:0;width:100%;padding:18px 5vw;display:flex;justify-content:space-between;align-items:center;color:#fff;background:linear-gradient(#071c13b0,transparent)}.rw-logo{font-weight:900;letter-spacing:.15em;color:white;text-decoration:none}.rw-logo span{color:var(--rw-leaf)}.rw-navlinks{display:flex;align-items:center;gap:24px}.rw-navlinks a{color:white;text-decoration:none;font-size:.85rem}.rw-feature-menu-wrap{position:relative}.rw-feature-menu-trigger{display:flex;align-items:center;gap:7px;border:0;background:transparent;color:white;font:inherit;font-size:.85rem;cursor:pointer;padding:8px 0}.rw-menu-chevron{font-size:1rem;transition:transform .2s}.rw-feature-menu-trigger.open .rw-menu-chevron{transform:rotate(180deg)}.rw-feature-dropdown{position:absolute;right:0;top:calc(100% + 12px);width:245px;padding:7px;background:#f4f3e9;border:1px solid #ffffff50;border-radius:13px;box-shadow:0 14px 38px #061b1280;z-index:50}.rw-feature-dropdown button{display:flex;align-items:center;gap:11px;width:100%;padding:10px 11px;border:0;border-radius:8px;background:transparent;color:#183629;text-align:left;font-size:.72rem;font-weight:750;letter-spacing:.035em;cursor:pointer;white-space:nowrap}.rw-feature-dropdown button:hover{background:#e4ecd9}.rw-feature-dropdown button span{color:#6f925b;font-size:.66rem;font-weight:900}
        .rw-opening{position:relative;color:white;background:#0c291d;isolation:isolate;overflow:hidden}.rw-video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-2}.rw-opening:before{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(90deg,#071c13b5,#071c1338 68%),linear-gradient(0deg,#0c291d 0%,transparent 35%);pointer-events:none}
        .rw-hero{height:100vh;min-height:650px;display:flex;align-items:center;padding:10vw 9vw 14vw;position:relative}.rw-hero-copy{max-width:850px;animation:rw-rise 1.1s ease both}.rw-eyebrow{text-transform:uppercase;letter-spacing:.2em;font-size:.7rem;font-weight:800;color:#d4e9c4}.rw-hero h1{font-size:clamp(4.5rem,12vw,10rem);line-height:.83;letter-spacing:-.085em;margin:22px 0;font-weight:900}.rw-hero h1 span{color:var(--rw-leaf)}.rw-hero p{max-width:560px;font-size:clamp(1rem,2vw,1.3rem);line-height:1.65;color:#edf4e9}.rw-primary{display:inline-block;border:0;border-radius:99px;background:var(--rw-leaf);color:#173326;padding:14px 21px;font-weight:850;cursor:pointer;margin-top:14px;transition:.25s}.rw-primary:hover{transform:translateY(-3px);background:#e2efcf}.rw-scroll{position:absolute;bottom:48px;left:9vw;font-size:.7rem;letter-spacing:.2em;text-transform:uppercase}
        .rw-farm-intro{min-height:72vh;padding:90px 7vw 110px;display:grid;place-items:center;position:relative;text-align:center}.rw-farm-copy{width:min(850px,100%)}.rw-farm-copy h2{font-size:clamp(2.6rem,6vw,5rem);letter-spacing:-.075em;margin:12px 0;color:white}.rw-farm-copy p{max-width:600px;margin:0 auto;color:#e8f0e5;line-height:1.7}.rw-farm-cta{margin-top:28px;background:#f6f7ef;color:#173a2a;border:0;border-radius:18px;padding:22px 30px;font:inherit;font-size:1.05rem;font-weight:850;cursor:pointer;box-shadow:0 15px 50px #061b1260;transition:.25s}.rw-farm-cta:hover{transform:translateY(-4px);background:var(--rw-leaf)}.rw-farm-note{font-size:.8rem!important;color:#d5e3d0!important;margin-top:16px!important}
        .rw-features{position:relative;background:#0c291d;color:white}.rw-scene{height:100vh;min-height:650px;position:sticky;top:0;overflow:hidden;background:#102d20}.rw-scene-img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transform:scale(1.05);transition:opacity 1.1s ease,transform 6s ease}.rw-scene-img.active{opacity:1;transform:scale(1)}.rw-scene:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#061b13a8,#061b1320 75%),linear-gradient(0deg,#061b1370,transparent 55%);z-index:1;pointer-events:none}.rw-scene-heading{position:absolute;z-index:2;left:7vw;right:auto;top:50%;width:min(410px,40vw);max-width:410px;transform:translate3d(0,-50%,0);transition:transform 2.2s cubic-bezier(.16,1,.3,1),opacity .6s ease;will-change:transform;pointer-events:none}.rw-scene-heading.side-right{transform:translate3d(calc(100vw - 14vw - min(410px,40vw)),-50%,0)}.rw-scene-heading h2{font-size:clamp(2.5rem,4.6vw,4.7rem);letter-spacing:-.07em;line-height:.94;margin:16px 0}.rw-scene-heading p{line-height:1.75;color:#e1ecdf;font-size:1.02rem;max-width:390px;margin-top:18px}
        .rw-feature-track{position:relative;margin-top:-100vh;z-index:3;pointer-events:none}.rw-feature-step{height:100vh;min-height:650px;display:flex;align-items:center;justify-content:flex-end;padding:0 8vw}.rw-feature-step.card-left{justify-content:flex-start}.rw-feature-card{width:min(440px,90vw);padding:30px;border:1px solid #ffffff55;border-radius:26px;background:#103b2cce;backdrop-filter:blur(18px);box-shadow:0 25px 90px #061b1290;pointer-events:auto;opacity:0;transform:translateY(60px) scale(.95);transition:opacity .75s,transform .75s cubic-bezier(.2,.75,.2,1)}.rw-feature-card.visible{opacity:1;transform:translateY(0) scale(1)}.rw-feature-num{font-size:.7rem;letter-spacing:.18em;color:#c6e2af;font-weight:850}.rw-feature-card h3{font-size:2.25rem;letter-spacing:-.06em;margin:14px 0 10px}.rw-feature-card p{color:#d9e6d6;line-height:1.65}.rw-feature-card button{border:0;border-radius:99px;background:var(--rw-leaf);color:#173326;padding:13px 18px;font-weight:850;cursor:pointer;margin-top:10px}
        .rw-end{padding:110px 24px;text-align:center;background:var(--rw-cream);color:var(--rw-ink)}.rw-end .rw-eyebrow{color:#56804b}.rw-end h2{font-size:clamp(2.5rem,6vw,5rem);letter-spacing:-.07em;max-width:800px;margin:12px auto}.rw-end p{max-width:600px;margin:auto;color:#637468;line-height:1.7}
        .rw-dots{position:fixed;right:24px;top:50%;transform:translateY(-50%);z-index:20;display:grid;gap:12px}.rw-dot{height:8px;width:8px;border-radius:50%;border:1px solid white;background:#ffffff50;padding:0;cursor:pointer}.rw-dot.active{background:var(--rw-leaf);transform:scale(1.6)}
        .rw-modal{position:fixed;inset:0;background:#061a12d9;z-index:60;display:grid;place-items:center;padding:18px;backdrop-filter:blur(9px);overflow:auto}.rw-modalbox{max-width:620px;width:100%;max-height:92vh;overflow:auto;padding:30px;border-radius:25px;background:#f7f7ef;color:var(--rw-ink);position:relative;box-shadow:0 25px 90px #0005}.rw-modalbox h2{font-size:clamp(2rem,5vw,3rem);letter-spacing:-.06em;margin:10px 0}.rw-modalbox p{line-height:1.6;color:#607166}.rw-close{position:sticky;float:right;top:0;border:0;background:#e8eee3;border-radius:50%;width:34px;height:34px;font-size:1.35rem;cursor:pointer;z-index:2}.rw-tabs{display:flex;gap:6px;background:#e8eee3;border-radius:99px;padding:5px;margin:20px 0}.rw-tabs button{flex:1;border:0;border-radius:99px;padding:11px;background:transparent;color:#385344;font-weight:800;cursor:pointer}.rw-tabs button.active{background:#173e2d;color:white}.rw-field{width:100%;padding:13px 14px;margin:6px 0 12px;border:1px solid #dbe4d8;border-radius:11px;background:white;font:inherit;color:#173326}.rw-label{display:block;font-size:.82rem;font-weight:800;margin:8px 0 2px;color:#385344}.rw-form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}.rw-choice-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:20px 0}.rw-choice{border:1px solid #dbe4d8;border-radius:15px;padding:16px 10px;background:white;cursor:pointer;text-align:center;font:inherit;color:#173326;transition:.2s}.rw-choice:hover{border-color:#729b63;transform:translateY(-2px)}.rw-choice strong{display:block;margin-top:8px;font-size:.9rem}.rw-choice small{display:block;color:#718074;font-size:.72rem;margin-top:4px}.rw-choice span{font-size:1.5rem}.rw-submit:disabled{opacity:.65;cursor:not-allowed}.rw-submit{width:100%;border:0;border-radius:99px;background:#173e2d;color:white;padding:15px;font-weight:850;margin-top:12px;cursor:pointer}.rw-secondary{border:1px solid #b9cbb2;background:transparent;color:#31543e;border-radius:99px;padding:11px 16px;font-weight:800;cursor:pointer}.rw-helper{font-size:.78rem!important;color:#7a887d!important}.rw-step-label{color:#628258;font-size:.7rem;font-weight:900;letter-spacing:.17em;text-transform:uppercase}.rw-notice{background:#fbe8df;color:#8b3525;border-radius:10px;padding:10px;font-size:.85rem;margin:10px 0}.rw-sample-note{background:#e8f1e1;color:#31543e;border-radius:12px;padding:11px 13px;font-size:.82rem;margin:12px 0}.rw-form-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}.rw-form-actions .rw-submit{flex:1;margin-top:0;min-width:220px}
        @keyframes rw-rise{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
        @media(max-width:720px){.rw-nav{padding:16px 20px}.rw-navlinks a{display:none}.rw-feature-dropdown{right:0;width:min(245px,85vw)}.rw-hero{padding:25px;min-height:700px}.rw-scroll{left:25px}.rw-farm-intro{padding:70px 22px;min-height:65vh}.rw-scene{min-height:700px}.rw-scene-heading{left:7vw;right:7vw;top:8vh;width:auto;transform:none;max-width:unset}.rw-scene-heading.side-right{left:7vw;right:7vw;top:8vh;width:auto;transform:none;max-width:unset}.rw-scene-heading h2{font-size:2.7rem}.rw-scene-heading p{font-size:.92rem;max-width:560px;margin-top:10px}.rw-feature-step{justify-content:center;align-items:flex-end;padding:0 16px 9vh;min-height:700px}.rw-feature-step.card-left{justify-content:center}.rw-feature-card{margin:0!important;padding:23px}.rw-feature-card h3{font-size:1.9rem}.rw-dots{right:11px}.rw-choice-grid{grid-template-columns:1fr}.rw-form-grid{grid-template-columns:1fr}.rw-modalbox{padding:23px}}
      `}</style>
    </main>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return <div><label className="rw-label">{label}</label><input className="rw-field" type={type} value={value} onChange={(event) => onChange(event.target.value)} /></div>;
}

function SelectField({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return <div>{label && <label className="rw-label">{label}</label>}<select className="rw-field" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option}>{option}</option>)}</select></div>;
}
