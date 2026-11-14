// Comprehensive sample & fallback data for RootWise M4 Dashboard

export type Language = "en" | "kn";

export interface StatusMetric {
  title: string;
  value: string;
  status: string;
  statusType: "good" | "warning" | "alert";
  source: string;
  date: string;
  icon: string;
}

export interface RotationStrategy {
  id: string;
  name: string;
  nameKn: string;
  cropSequence: string;
  yieldScore: number;
  soilHealthScore: number;
  waterEfficiency: number;
  netMarginInr: number;
  carbonScore: number;
  pestBreakScore: number;
  rank: number;
  rankChange: number;
  simulatedScore?: number;
  benefits: string[];
  risks: string[];
  dataUsed: string[];
  missingInfo: string[];
  needsLocalReview: boolean;
}

export interface RadarDataPoint {
  metric: string;
  metricKn: string;
  conventional: number;
  legume: number;
  millet: number;
  pulseOilseed: number;
}

export interface SoilStressMonth {
  month: string;
  monthKn: string;
  surfaceStress: number; // 0 - 100
  rootStress: number;
  subsoilStress: number;
  moistureVolumetric: number; // %
  advice: string;
  adviceKn: string;
}

export interface YieldTrajectoryPoint {
  season: string;
  medianYield: number;
  lowerConfidence: number;
  upperConfidence: number;
  historical: boolean;
  benchmark: number;
}

export const sampleStatusMetrics: StatusMetric[] = [
  {
    title: "Soil Moisture (Volumetric)",
    value: "28.4%",
    status: "Optimal Moisture Level",
    statusType: "good",
    source: "Sentinel-1 SAR & In-Situ Sensor",
    date: "14 Nov 2026, 06:00 IST",
    icon: "💧",
  },
  {
    title: "Crop Cycle Phase",
    value: "Rabi Sowing / Vegetative",
    status: "Day 36 of 120 (On Track)",
    statusType: "good",
    source: "ICAR Crop Phenology Model",
    date: "Rabi Season 2026-27",
    icon: "🌱",
  },
  {
    title: "Rainfall & UV Stress",
    value: "42 mm · UV Index 6.2",
    status: "Moderate Evapotranspiration",
    statusType: "warning",
    source: "IMD Agromet Grid (0.25°)",
    date: "Updated 3 hrs ago",
    icon: "☀️",
  },
];

export const sampleStrategies: RotationStrategy[] = [
  {
    id: "legume-restoration",
    name: "Soil Restoration (Legume Intercrop)",
    nameKn: "ಮಣ್ಣು ಸುಧಾರಣೆ (ದ್ವಿದಳ ಧಾನ್ಯ ಅಂತರಬೆಳೆ)",
    cropSequence: "Soybean + Pigeonpea → Chickpea",
    yieldScore: 84,
    soilHealthScore: 92,
    waterEfficiency: 78,
    netMarginInr: 41200,
    carbonScore: 88,
    pestBreakScore: 85,
    rank: 1,
    rankChange: 0,
    benefits: [
      "Fixes 38-45 kg biological nitrogen per hectare naturally",
      "Breaks continuous cereal pest & stem-borer cycles",
      "Increases soil organic matter by up to 0.22% per cycle",
      "Reduces chemical fertilizer costs by ₹3,200/acre",
    ],
    risks: [
      "Susceptible to waterlogging during heavy late-monsoon downpours",
      "Requires synchronized harvesting for intercropped pigeonpea",
      "Market price volatility for chickpea during peak arrival season",
    ],
    dataUsed: [
      "ICAR All India Coordinated Research Project on Pulses",
      "Sentinel-2 10m NDVI Canopy Greenness Time Series",
      "District Agromet Soil Survey & Texture Map",
    ],
    missingInfo: [
      "Subsoil compaction profile below 40cm depth",
      "Local field-level rhizobial inoculation efficacy test",
    ],
    needsLocalReview: true,
  },
  {
    id: "millet-resilient",
    name: "Climate-Resilient Millets",
    nameKn: "ಹವಾಮಾನ-ಸ್ಥಿತಿಸ್ಥಾಪಕ ಸಿರಿಧಾನ್ಯಗಳು",
    cropSequence: "Finger Millet (Ragi) → Sorghum (Jowar)",
    yieldScore: 76,
    soilHealthScore: 74,
    waterEfficiency: 95,
    netMarginInr: 34500,
    carbonScore: 72,
    pestBreakScore: 80,
    rank: 2,
    rankChange: 0,
    benefits: [
      "Requires 40% less water than maize or paddy rotations",
      "C4 photosynthetic efficiency resists temperatures up to 41°C",
      "High dietary fiber & nutritional value with growing urban market demand",
      "Extremely hardy against drought spells exceeding 21 days",
    ],
    risks: [
      "Lower gross tonnage compared to high-input hybrid maize",
      "Bird damage risk during grain filling stage in isolated millet plots",
      "Requires dry storage facilities to prevent grain molding",
    ],
    dataUsed: [
      "ICRISAT Dryland Cereals Genetic Improvement Database",
      "ECMWF ERA5 Precipitation & Temperature Reanalysis",
      "Local Mandi Daily Minimum Support Price (MSP) Realization",
    ],
    missingInfo: [
      "Certified drought-tolerant seed availability in local taluk RSK",
      "Micro-drip irrigation response coefficients under drought",
    ],
    needsLocalReview: false,
  },
  {
    id: "pulse-oilseed",
    name: "Pulse & Oilseed Diversification",
    nameKn: "ದ್ವಿದಳ ಮತ್ತು ಎಣ್ಣೆಕಾಳು ವೈವಿಧ್ಯತೆ",
    cropSequence: "Groundnut → Mustard / Green Gram",
    yieldScore: 80,
    soilHealthScore: 82,
    waterEfficiency: 82,
    netMarginInr: 43800,
    carbonScore: 76,
    pestBreakScore: 82,
    rank: 3,
    rankChange: 0,
    benefits: [
      "High commercial cash value in local agricultural markets",
      "Taproot architecture utilizes residual subsoil moisture efficiently",
      "Nutrient-dense crop residues provide premium cattle fodder",
    ],
    risks: [
      "Aflatoxin risk in groundnut if drying conditions are humid",
      "Aphid attack vulnerability in mustard under warm cloudy skies",
      "Higher initial working capital required for quality certified seeds",
    ],
    dataUsed: [
      "ICAR-Directorate of Groundnut Research Agronomy Standards",
      "Mandi Trade Volume & Wholesale Price Index (WPI)",
      "Sentinel-1 SAR Soil Surface Wetness Anomaly Series",
    ],
    missingInfo: [
      "Soil Boron and Calcium availability levels for pod filling",
    ],
    needsLocalReview: true,
  },
  {
    id: "conventional",
    name: "Conventional Sequence",
    nameKn: "ಸಾಂಪ್ರದಾಯಿಕ ಬೆಳೆ ಕ್ರಮ",
    cropSequence: "Cotton / Paddy → Wheat / Fallow",
    yieldScore: 78,
    soilHealthScore: 52,
    waterEfficiency: 54,
    netMarginInr: 32800,
    carbonScore: 48,
    pestBreakScore: 42,
    rank: 4,
    rankChange: 0,
    benefits: [
      "Familiar farming routine with established merchant relationships",
      "Existing equipment, sprayers, and labor practices ready to deploy",
      "Well-known harvesting and local procurement channels",
    ],
    risks: [
      "Heavy reliance on synthetic urea, causing soil acidification",
      "High susceptibility to pink bollworm and blast fungus epidemics",
      "Rapid depletion of groundwater table in tube-well irrigated zones",
    ],
    dataUsed: [
      "Historical Farm Logbook & Survey Records",
      "District Fertilizer Consumption Statistics",
    ],
    missingInfo: [
      "Long-term pesticide resistance buildup data in local soil fauna",
    ],
    needsLocalReview: true,
  },
];

export const sampleRadarData: RadarDataPoint[] = [
  {
    metric: "Soil Health",
    metricKn: "ಮಣ್ಣಿನ ಆರೋಗ್ಯ",
    conventional: 52,
    legume: 92,
    millet: 74,
    pulseOilseed: 82,
  },
  {
    metric: "Water Efficiency",
    metricKn: "ನೀರಿನ ದಕ್ಷತೆ",
    conventional: 54,
    legume: 78,
    millet: 95,
    pulseOilseed: 82,
  },
  {
    metric: "Net Profit Stability",
    metricKn: "ಲಾಭ ಸ್ಥಿರತೆ",
    conventional: 60,
    legume: 86,
    millet: 78,
    pulseOilseed: 90,
  },
  {
    metric: "Yield Resilience",
    metricKn: "ಇಳುವರಿ ಸ್ಥಿತಿಸ್ಥಾಪಕತ್ವ",
    conventional: 62,
    legume: 84,
    millet: 92,
    pulseOilseed: 79,
  },
  {
    metric: "Pest Cycle Break",
    metricKn: "ಕೀಟ ಚಕ್ರ ಮುರಿತ",
    conventional: 42,
    legume: 85,
    millet: 80,
    pulseOilseed: 82,
  },
  {
    metric: "Input Cost Saving",
    metricKn: "ವೆಚ್ಚ ಉಳಿತಾಯ",
    conventional: 45,
    legume: 88,
    millet: 85,
    pulseOilseed: 75,
  },
];

export const sampleSoilStressCalendar: SoilStressMonth[] = [
  {
    month: "Jan",
    monthKn: "ಜನ",
    surfaceStress: 22,
    rootStress: 18,
    subsoilStress: 15,
    moistureVolumetric: 31,
    advice: "Optimal moisture for Rabi vegetative growth.",
    adviceKn: "ರಬಿ ಸಸ್ಯ ಬೆಳವಣಿಗೆಗೆ ಸೂಕ್ತ ತೇವಾಂಶ.",
  },
  {
    month: "Feb",
    monthKn: "ಫೆಬ್ರ",
    surfaceStress: 35,
    rootStress: 28,
    subsoilStress: 20,
    moistureVolumetric: 26,
    advice: "Grain filling stage; schedule light protective irrigation if rain fails.",
    adviceKn: "ಕಾಳು ತುಂಬುವ ಹಂತ; ಮಳೆಯಾಗದಿದ್ದರೆ ಹಗುರ ರಕ್ಷಣಾತ್ಮಕ ನೀರಾವರಿ ನೀಡಿ.",
  },
  {
    month: "Mar",
    monthKn: "ಮಾರ್ಚ್",
    surfaceStress: 68,
    rootStress: 52,
    subsoilStress: 32,
    moistureVolumetric: 19,
    advice: "Rising temperatures; harvest Rabi crops before seed shattering.",
    adviceKn: "ಹೆಚ್ಚುತ್ತಿರುವ ಉಷ್ಣತೆ; ಬೀಜ ಉದುರುವ ಮುನ್ನ ರಬಿ ಬೆಳೆ ಕಟಾವು ಮಾಡಿ.",
  },
  {
    month: "Apr",
    monthKn: "ಏಪ್ರಿ",
    surfaceStress: 88,
    rootStress: 74,
    subsoilStress: 48,
    moistureVolumetric: 14,
    advice: "Severe heat stress; keep land covered with mulch or green manure crop.",
    adviceKn: "ತೀವ್ರ ಬಿಸಿಲಿನ ಒತ್ತಡ; ಭೂಮಿಯನ್ನು ಹೊದಿಕೆ ಅಥವಾ ಹಸಿರೆಲೆ ಗೊಬ್ಬರದಿಂದ ಮುಚ್ಚಿ.",
  },
  {
    month: "May",
    monthKn: "ಮೇ",
    surfaceStress: 82,
    rootStress: 68,
    subsoilStress: 44,
    moistureVolumetric: 16,
    advice: "Pre-monsoon showers expected; begin summer plowing for pest aeration.",
    adviceKn: "ಮುಂಗಾರು ಪೂರ್ವ ಮಳೆ ನಿರೀಕ್ಷೆ; ಕೀಟ ನಿಯಂತ್ರಣಕ್ಕಾಗಿ ಬೇಸಿಗೆ ಉಳುಮೆ ಆರಂಭಿಸಿ.",
  },
  {
    month: "Jun",
    monthKn: "ಜೂನ್",
    surfaceStress: 38,
    rootStress: 32,
    subsoilStress: 30,
    moistureVolumetric: 27,
    advice: "Monsoon onset; sow Kharif legume or millet after receiving 50mm rain.",
    adviceKn: "ಮುಂಗಾರು ಆರಂಭ; 50ಮಿಮೀ ಮಳೆಯ ನಂತರ ಮುಂಗಾರು ದ್ವಿದಳ ಅಥವಾ ಸಿರಿಧಾನ್ಯ ಬಿತ್ತನೆ ಮಾಡಿ.",
  },
  {
    month: "Jul",
    monthKn: "ಜುಲೈ",
    surfaceStress: 15,
    rootStress: 14,
    subsoilStress: 18,
    moistureVolumetric: 34,
    advice: "Active monsoon; ensure field drainage channels to prevent root asphyxia.",
    adviceKn: "ಸಕ್ರಿಯ ಮುಂಗಾರು; ಬೇರು ಕೊಳೆಯುವುದನ್ನು ತಪ್ಪಿಸಲು ಬಸಿಗಾಲುವೆ ಸರಿಪಡಿಸಿ.",
  },
  {
    month: "Aug",
    monthKn: "ಆಗ",
    surfaceStress: 18,
    rootStress: 16,
    subsoilStress: 15,
    moistureVolumetric: 33,
    advice: "Vegetative peak; perform inter-cultivation weeding and mulching.",
    adviceKn: "ಸಸ್ಯ ಸಮೃದ್ಧಿಯ ಹಂತ; ಎಡೆಕುಂಟೆ ಹೊಡೆದು ಕಳೆ ನಿಯಂತ್ರಿಸಿ.",
  },
  {
    month: "Sep",
    monthKn: "ಸೆಪ್ಟೆಂ",
    surfaceStress: 28,
    rootStress: 22,
    subsoilStress: 19,
    moistureVolumetric: 29,
    advice: "Retreating monsoon showers; initiate planning for moisture-conserving Rabi crops.",
    adviceKn: "ಹಿಂಗಾರು ಪೂರ್ವ ಮಳೆ; ತೇವಾಂಶ ಉಳಿಸುವ ರಬಿ ಬೆಳೆಗಳ ಯೋಜನೆ ಪ್ರಾರಂಭಿಸಿ.",
  },
  {
    month: "Oct",
    monthKn: "ಅಕ್ಟೋ",
    surfaceStress: 32,
    rootStress: 26,
    subsoilStress: 22,
    moistureVolumetric: 27,
    advice: "Kharif harvest and land preparation for winter chickpea/sorghum.",
    adviceKn: "ಮುಂಗಾರು ಕಟಾವು ಮತ್ತು ಚಳಿಗಾಲದ ಕಡಲೆ/ಜೋಳಕ್ಕಾಗಿ ಭೂಮಿ ಸಿದ್ಧತೆ.",
  },
  {
    month: "Nov",
    monthKn: "ನವೆಂ",
    surfaceStress: 25,
    rootStress: 20,
    subsoilStress: 18,
    moistureVolumetric: 28,
    advice: "Sow Rabi crops in residual moisture with zero-till or minimum-till.",
    adviceKn: "ಉಳಿದ ತೇವಾಂಶದಲ್ಲಿ ಕನಿಷ್ಠ ಉಳುಮೆಯೊಂದಿಗೆ ರಬಿ ಬೆಳೆ ಬಿತ್ತನೆ ಮಾಡಿ.",
  },
  {
    month: "Dec",
    monthKn: "ಡಿಸೆಂ",
    surfaceStress: 24,
    rootStress: 21,
    subsoilStress: 17,
    moistureVolumetric: 29,
    advice: "Cool temperatures minimize evapotranspiration; monitor soil moisture.",
    adviceKn: "ತಂಪಾದ ಹವಾಮಾನದಿಂದ ನೀರಾವರಿ ಆವಿಯಾಗುವಿಕೆ ಕಡಿಮೆ; ಮಣ್ಣಿನ ತೇವಾಂಶ ಗಮನಿಸಿ.",
  },
];

export const sampleYieldTrajectories: YieldTrajectoryPoint[] = [
  { season: "Kharif '22", medianYield: 72, lowerConfidence: 66, upperConfidence: 78, historical: true, benchmark: 70 },
  { season: "Rabi '22", medianYield: 74, lowerConfidence: 68, upperConfidence: 80, historical: true, benchmark: 71 },
  { season: "Kharif '23", medianYield: 69, lowerConfidence: 62, upperConfidence: 75, historical: true, benchmark: 72 },
  { season: "Rabi '23", medianYield: 77, lowerConfidence: 70, upperConfidence: 83, historical: true, benchmark: 73 },
  { season: "Kharif '24", medianYield: 79, lowerConfidence: 73, upperConfidence: 85, historical: true, benchmark: 74 },
  { season: "Rabi '24", medianYield: 81, lowerConfidence: 75, upperConfidence: 87, historical: true, benchmark: 75 },
  { season: "Kharif '25", medianYield: 83, lowerConfidence: 76, upperConfidence: 89, historical: true, benchmark: 75 },
  { season: "Rabi '25", medianYield: 84, lowerConfidence: 77, upperConfidence: 91, historical: true, benchmark: 76 },
  { season: "Kharif '26", medianYield: 86, lowerConfidence: 79, upperConfidence: 93, historical: true, benchmark: 77 },
  { season: "Rabi '26 (Est)", medianYield: 88, lowerConfidence: 80, upperConfidence: 96, historical: false, benchmark: 77 },
  { season: "Kharif '27 (Proj)", medianYield: 91, lowerConfidence: 82, upperConfidence: 99, historical: false, benchmark: 78 },
];

export const glossaryTerms: Record<string, { en: string; kn: string }> = {
  "Biological Nitrogen Fixation": {
    en: "Process where leguminous crops convert atmospheric N2 into plant-usable nitrogen via root rhizobia bacteria, enriching soil naturally.",
    kn: "ದ್ವಿದಳ ಧಾನ್ಯದ ಬೆಳೆಗಳು ಬೇರಿನ ಗಂಟುಗಳಲ್ಲಿರುವ ಬ್ಯಾಕ್ಟೀರಿಯಾದ ಮೂಲಕ ಗಾಳಿಯಲ್ಲಿರುವ ಸಾರಜನಕವನ್ನು ಹೀರಿಕೊಂಡು ಮಣ್ಣಿಗೆ ಪೋಷಕಾಂಶ ಒದಗಿಸುವ ಪ್ರಕ್ರಿಯೆ.",
  },
  "Soil Organic Carbon (SOC)": {
    en: "The measurable organic carbon in soil, critical for moisture holding capacity, microbial life, and sustainable crop yields.",
    kn: "ಮಣ್ಣಿನಲ್ಲಿರುವ ಸಾವಯವ ಇಂಗಾಲ, ಇದು ನೀರು ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳುವ ಸಾಮರ್ಥ್ಯ ಮತ್ತು ಸೂಕ್ಷ್ಮಾಣು ಜೀವಿಗಳ ಆರೋಗ್ಯಕ್ಕೆ ಅತ್ಯಗತ್ಯ.",
  },
  "Stress Window": {
    en: "A vulnerable seasonal timeframe where high heat and low soil moisture threaten crop flowering, pollination, or germination.",
    kn: "ಹೆಚ್ಚಿನ ಶಾಖ ಮತ್ತು ಕಡಿಮೆ ತೇವಾಂಶದಿಂದಾಗಿ ಬೆಳೆಯ ಹೂವಾಡುವಿಕೆ ಅಥವಾ ಬೆಳವಣಿಗೆಗೆ ಅಡ್ಡಿಯಾಗುವ ನಿರ್ಣಾಯಕ ಋತುಮಾನ ಅವಧಿ.",
  },
  "C4 Photosynthesis": {
    en: "An efficient photosynthetic mechanism in crops like ragi and jowar that captures carbon while losing drastically less water under intense heat.",
    kn: "ರಾಗಿ ಮತ್ತು ಜೋಳದಂತಹ ಬೆಳೆಗಳಲ್ಲಿ ಕಂಡುಬರುವ ದಕ್ಷ ದ್ಯುತಿಸಂಶ್ಲೇಷಣಾ ವಿಧಾನ, ಇದು ಬಿಸಿಲಿನಲ್ಲಿ ಕಡಿಮೆ ನೀರನ್ನು ಬಳಸಿ ಹೆಚ್ಚು ಆಹಾರ ತಯಾರಿಸುತ್ತದೆ.",
  },
  "Confidence Band": {
    en: "Statistical 90% confidence envelope computed from satellite SAR backscatter, NDVI time-series, and local ground calibrations.",
    kn: "ಉಪಗ್ರಹ ರೇಡಾರ್, ಹಸಿರು ಸೂಚ್ಯಂಕ ಮತ್ತು ಸ್ಥಳೀಯ ಮಣ್ಣಿನ ಪರೀಕ್ಷೆಯಿಂದ ಲೆಕ್ಕಹಾಕಲಾದ ಶೇ 90ರ ಸಂಭವನೀಯತೆಯ ನಂಬಿಕೆ ಪಟ್ಟಿ.",
  },
};
