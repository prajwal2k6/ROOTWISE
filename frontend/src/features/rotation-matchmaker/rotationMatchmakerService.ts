export type RotationPathway = {
  number: string;
  title: string;
  sequence: string;
  purpose: string;
  checks: string;
};

export const SUGGESTED_PATHWAYS: RotationPathway[] = [
  {
    number: "01",
    title: "Legume break",
    sequence: "Current crop → suitable legume → next planned crop",
    purpose: "Explore whether a legume phase could diversify the sequence.",
    checks: "Local legume suitability, soil condition, water needs and pest history.",
  },
  {
    number: "02",
    title: "Alternate crop families",
    sequence: "Cereal → legume → cereal",
    purpose: "Compare alternating crop families with repeating the same crop family.",
    checks: "Specific crop varieties, sowing windows, nutrient needs and local advice.",
  },
  {
    number: "03",
    title: "Diversified sequence",
    sequence: "Cereal → legume → another crop family",
    purpose: "Explore a longer sequence that includes more than two crop families.",
    checks: "Market access, labour, irrigation and whether each crop fits the season.",
  },
];

export function getSuggestedPathways(): RotationPathway[] {
  return SUGGESTED_PATHWAYS;
}
