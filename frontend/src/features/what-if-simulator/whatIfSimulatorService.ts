export type WhatIfScenario = {
  rainfall: number;
  temperature: number;
  monsoon: string;
};

export const DEFAULT_SCENARIO: WhatIfScenario = {
  rainfall: 0,
  temperature: 0,
  monsoon: "Usual timing",
};

export const MONSOON_OPTIONS = [
  "Early by 2 weeks",
  "Usual timing",
  "Delayed by 2 weeks",
  "Delayed by 4 weeks",
];
