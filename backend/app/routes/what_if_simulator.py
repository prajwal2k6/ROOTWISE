from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/what-if-simulator", tags=["What-if Simulator"])


class SimulationRequest(BaseModel):
    temperature_delta: float = 0.0      # in °C, e.g. -2 to +5
    rainfall_delta_percent: float = 0.0 # in %, e.g. -50 to +50
    preset: Optional[str] = "Normal Year"
    farm_id: Optional[int] = None


class StrategySimulationResult(BaseModel):
    id: str
    name: str
    crop_sequence: str
    base_yield_score: float
    simulated_yield_score: float
    soil_stress_index: float
    water_deficit_risk: str
    net_margin_inr: int
    rank: int
    rank_change: int  # positive means moved up (e.g. +1), negative moved down
    confidence_level: str
    notes: str


class SimulationResponse(BaseModel):
    scenario: dict
    strategies: List[StrategySimulationResult]
    summary: str


@router.post("/simulate", response_model=SimulationResponse)
def simulate_scenario(req: SimulationRequest):
    temp = req.temperature_delta
    rain = req.rainfall_delta_percent

    # Baseline strategies
    # 1. Conventional Monoculture (e.g., Continuous Paddy/Wheat or Cotton)
    # 2. Legume-Intercrop Soil Restoration (e.g., Soybean/Pigeonpea -> Chickpea)
    # 3. Climate-Resilient Millets (e.g., Finger Millet/Pearl Millet -> Sorghum)
    # 4. High-Value Pulse & Oilseed (e.g., Groundnut -> Mustard/Green Gram)

    # Calculate sensitivity penalties/bonuses
    # Conventional: highly vulnerable to drought (-rain) and heat (+temp)
    conv_yield = max(20.0, min(100.0, 78.0 + (rain * 0.45) - (temp * 4.8)))
    conv_stress = min(95.0, max(15.0, 45.0 - (rain * 0.4) + (temp * 5.2)))
    conv_margin = int(conv_yield * 420)

    # Legume Soil Restoration: moderate drought resilience, excellent soil health
    legume_yield = max(30.0, min(100.0, 82.0 + (rain * 0.25) - (temp * 3.2)))
    legume_stress = min(90.0, max(10.0, 32.0 - (rain * 0.3) + (temp * 3.5)))
    legume_margin = int(legume_yield * 490)

    # Millet-Sorghum Climate Resilient: C4 crops, thrives in heat, drought-proof
    millet_yield = max(40.0, min(100.0, 75.0 + (rain * 0.10) - (temp * 1.1) + (1.5 if temp > 1.5 else 0)))
    millet_stress = min(80.0, max(8.0, 22.0 - (rain * 0.15) + (temp * 1.8)))
    millet_margin = int(millet_yield * 450)

    # Pulse-Oilseed: good market value, moderate drought resilience
    pulse_yield = max(25.0, min(100.0, 80.0 + (rain * 0.30) - (temp * 3.8)))
    pulse_stress = min(90.0, max(12.0, 36.0 - (rain * 0.35) + (temp * 4.0)))
    pulse_margin = int(pulse_yield * 520)

    # Rank them based on simulated yield score and resilience
    items = [
        {
            "id": "legume-restoration",
            "name": "Soil Restoration (Legume Intercrop)",
            "crop_sequence": "Soybean + Pigeonpea → Chickpea",
            "base_yield_score": 82.0,
            "sim_score": round(legume_yield, 1),
            "stress": round(legume_stress, 1),
            "deficit": "Low" if legume_stress < 35 else ("Moderate" if legume_stress < 60 else "Elevated"),
            "margin": legume_margin,
            "confidence": "High (Lab & ICAR Data)",
            "notes": "Biological nitrogen fixation provides continuous soil replenishment.",
            "base_rank": 1,
        },
        {
            "id": "pulse-oilseed",
            "name": "Pulse & Oilseed Diversification",
            "crop_sequence": "Groundnut → Mustard / Green Gram",
            "base_yield_score": 80.0,
            "sim_score": round(pulse_yield, 1),
            "stress": round(pulse_stress, 1),
            "deficit": "Low" if pulse_stress < 40 else ("Moderate" if pulse_stress < 65 else "High"),
            "margin": pulse_margin,
            "confidence": "Moderate-High (Market Verified)",
            "notes": "High net cash returns with moderate taproot water extraction.",
            "base_rank": 2,
        },
        {
            "id": "conventional",
            "name": "Conventional Sequence",
            "crop_sequence": "Cotton / Paddy → Wheat / Fallow",
            "base_yield_score": 78.0,
            "sim_score": round(conv_yield, 1),
            "stress": round(conv_stress, 1),
            "deficit": "Low" if conv_stress < 40 else ("Elevated" if conv_stress < 70 else "Severe"),
            "margin": conv_margin,
            "confidence": "High (Historical Farm Practice)",
            "notes": "High input requirements and steep penalties during rainfall deficits.",
            "base_rank": 3,
        },
        {
            "id": "millet-resilient",
            "name": "Climate-Resilient Millets",
            "crop_sequence": "Finger Millet (Ragi) → Sorghum (Jowar)",
            "base_yield_score": 75.0,
            "sim_score": round(millet_yield, 1),
            "stress": round(millet_stress, 1),
            "deficit": "Low" if millet_stress < 30 else ("Low-Moderate" if millet_stress < 50 else "Moderate"),
            "margin": millet_margin,
            "confidence": "High (ICRISAT Dryland Trials)",
            "notes": "C4 photosynthetic efficiency resists extreme heat and moisture stress.",
            "base_rank": 4,
        },
    ]

    # Sort descending by simulated yield score
    items_sorted = sorted(items, key=lambda x: x["sim_score"], reverse=True)

    results: List[StrategySimulationResult] = []
    for idx, item in enumerate(items_sorted):
        curr_rank = idx + 1
        rank_change = item["base_rank"] - curr_rank  # positive if improved (e.g. 4 -> 1 is +3)
        results.append(
            StrategySimulationResult(
                id=item["id"],
                name=item["name"],
                crop_sequence=item["crop_sequence"],
                base_yield_score=item["base_yield_score"],
                simulated_yield_score=item["sim_score"],
                soil_stress_index=item["stress"],
                water_deficit_risk=item["deficit"],
                net_margin_inr=item["margin"],
                rank=curr_rank,
                rank_change=rank_change,
                confidence_level=item["confidence"],
                notes=item["notes"],
            )
        )

    # Narrative summary
    top = results[0]
    if rain < -15 or temp > 2.0:
        summary = (
            f"Under heat stress ({'+' if temp > 0 else ''}{temp:.1f}°C) and dry conditions ({'+' if rain > 0 else ''}{rain:.1f}%), "
            f"'{top.name}' ranks #1 ({top.simulated_yield_score}/100) due to low water requirements and minimal stress index."
        )
    elif rain > 15:
        summary = (
            f"With above-average precipitation ({'+' if rain > 0 else ''}{rain:.1f}%), '{top.name}' leads performance "
            f"yielding ₹{top.net_margin_inr:,}/acre with optimal nutrient absorption."
        )
    else:
        summary = (
            f"Under near-normal conditions, '{top.name}' provides balanced soil rejuvenation "
            f"and stable economic returns ({top.simulated_yield_score}/100)."
        )

    return SimulationResponse(
        scenario={
            "temperature_delta": temp,
            "rainfall_delta_percent": rain,
            "preset": req.preset or "Custom",
        },
        strategies=results,
        summary=summary,
    )


@router.get("/simulate", response_model=SimulationResponse)
def simulate_get(
    temperature_delta: float = Query(0.0),
    rainfall_delta_percent: float = Query(0.0),
    preset: Optional[str] = Query("Normal Year"),
):
    return simulate_scenario(
        SimulationRequest(
            temperature_delta=temperature_delta,
            rainfall_delta_percent=rainfall_delta_percent,
            preset=preset,
        )
    )
