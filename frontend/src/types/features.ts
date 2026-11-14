export type AuthMode = "Login" | "Sign up";

export type OnboardingStep = "auth" | "location" | "farm";

export type FeatureInfo = {
  number: string;
  name: string;
  title: string;
  description: string;
  detail: string;
  image: string;
  action: string;
};

export const featureData: FeatureInfo[] = [
  {
    number: "01",
    name: "ROTATION MATCHMAKER",
    title: "Compare your next move.",
    description: "Weigh your current crop sequence against soil-restoration and climate-resilience rotations, with the trade-offs made clear.",
    detail: "Compare crop-sequence strategies, including benefits, risks, trade-offs and configurable scoring assumptions.",
    image: "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=2200&q=85",
    action: "Explore rotations",
  },
  {
    number: "02",
    name: "WHAT-IF SIMULATOR",
    title: "What if the season changes?",
    description: "Adjust rainfall or temperature assumptions and explore how different conditions could change the relative suitability of crop rotations.",
    detail: "Try user-defined scenarios, such as lower rainfall or higher average temperature. These are scenarios, not forecasts.",
    image: "https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=2200&q=85",
    action: "Try simulator",
  },
  {
    number: "03",
    name: "SOIL STRESS CALENDAR",
    title: "Know when your land needs attention.",
    description: "Spot seasonal windows that may bring low soil moisture, high temperatures or irregular rainfall—before planning your next crop.",
    detail: "Explore potentially vulnerable periods by season or month, using available environmental indicators.",
    image: "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=2200&q=85",
    action: "Explore calendar",
  },
  {
    number: "04",
    name: "LAND MEMORY",
    title: "Every field has a story.",
    description: "Explore historical rainfall, temperature, soil-moisture and vegetation patterns around your selected farm.",
    detail: "Review environmental patterns over time and understand what available observations can—and cannot—tell you.",
    image: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=2200&q=85",
    action: "Explore Land Memory",
  },
  {
    number: "05",
    name: "EVIDENCE & CONFIDENCE",
    title: "Understand the evidence.",
    description: "See which observations and farm details support each insight, along with uncertainty, limitations and missing data.",
    detail: "Review observations and local inputs behind each comparison, including data gaps and confidence limitations.",
    image: "/images/evidence-confidence.png",
    action: "Explore evidence",
  },
  {
    number: "06",
    name: "FARMER DASHBOARD",
    title: "Your farm, in one clear view.",
    description: "Bring together your farm profile, environmental indicators, seasonal stress and crop-rotation comparisons in one place.",
    detail: "A central workspace for farm details, available environmental indicators, maps and crop-rotation comparisons.",
    image: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=2200&q=85",
    action: "Open dashboard",
  },
];
