"""Versioned, validated contracts shared with M3/M4/M5.

Reference values are not observations. A missing value stays None, not a zero.
"""
from __future__ import annotations
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator

CRITERIA = ("water_use", "forage_value", "nitrogen_fixing", "erosion_reduction", "organic_matter", "market_suitability")

class SourceValue(BaseModel):
    value: float | None = None
    low: float | None = None
    high: float | None = None
    unit: str | None = None
    source_url: str | None = None
    source_detail: str | None = None
    proxy: bool = False
    kind: Literal["published_reference", "field_measurement", "user_reported", "modelled", "missing"] = "published_reference"
    variety: str | None = None

    @model_validator(mode="after")
    def validate_range(self):
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError("low must be <= high")
        return self

class Crop(BaseModel):
    id: str
    name: str
    kannada: str
    scientific_name: str
    category: str
    varieties: list[str] = Field(default_factory=list)
    nitrogen_fixing: bool
    water_need: SourceValue
    reference_duration: SourceValue
    kc: dict[str, float] | None = None
    kc_source_url: str | None = None
    kc_proxy: bool = False
    fao_stage_lengths: list[int] | None = None
    phenology_days: dict[str, int] | None = None
    phenology_source_url: str | None = None
    forage_crude_protein_pct_dm: SourceValue = Field(default_factory=lambda: SourceValue(kind="missing"))
    forage_material: str | None = None
    forage_note: str | None = None
    straw_yield_t_ha_reference: SourceValue = Field(default_factory=lambda: SourceValue(kind="missing"))
    observed_erosion_protection: str | None = None
    critical_growth_stages: list[str] = Field(default_factory=list)
    critical_growth_stages_source_url: str | None = None
    uses: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def phenology_order(self):
        if self.phenology_days:
            keys = ("sowing", "vegetative", "flowering", "grain_fill", "harvest")
            if not all(k in self.phenology_days for k in keys):
                raise ValueError("Phenology needs all five verified boundaries")
            values = [self.phenology_days[k] for k in keys]
            if values[0] != 0 or any(a >= b for a, b in zip(values,values[1:])):
                raise ValueError("Phenology boundaries must increase from day zero")
        return self

class Priorities(BaseModel):
    water_use: float = Field(1, ge=0, le=100)
    forage_value: float = Field(1, ge=0, le=100)
    nitrogen_fixing: float = Field(1, ge=0, le=100)
    erosion_reduction: float = Field(1, ge=0, le=100)
    organic_matter: float = Field(1, ge=0, le=100)
    market_suitability: float = Field(1, ge=0, le=100)

    def weights(self) -> dict[str, float]:
        raw = self.model_dump()
        total = sum(raw.values())
        return {k: (v / total if total else 0.0) for k,v in raw.items()}

class DailyClimate(BaseModel):
    date: date
    rain_mm: float | None = Field(None, ge=0)
    tmax_c: float | None = None
    rootzone_moisture_m3m3: float | None = Field(None, ge=0, le=1)
    et0_mm: float | None = Field(None, ge=0)
    # Must come from verified field observation or classified layer, never inferred from NDVI alone.
    bare_field_observed: bool | None = None

class Climate(BaseModel):
    source_id: str | None = None
    source_url: str | None = None
    data_kind: Literal["observed", "modelled", "illustrative", "missing"] = "missing"
    annual_rainfall_mm: float | None = Field(None, ge=0)
    seasonal_effective_rainfall_mm: float | None = Field(None, ge=0)
    seasonal_irrigation_mm: float | None = Field(None, ge=0)
    seasonal_etc_mm: float | None = Field(None, ge=0)
    seasonal_etc_by_crop_mm: dict[str,float] = Field(default_factory=dict)
    daily: list[DailyClimate] = Field(default_factory=list)
    coverage: float | None = Field(None, ge=0, le=1)
    spatial_resolution_km: float | None = Field(None, gt=0)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def nonnegative_etc(self):
        if any(v <= 0 for v in self.seasonal_etc_by_crop_mm.values()):
            raise ValueError("crop-specific ETc must be > 0 mm")
        if len({x.date for x in self.daily}) != len(self.daily):
            raise ValueError("duplicate dates in climate.daily")
        return self

class MarketObservation(BaseModel):
    price_inr_per_quintal: float = Field(gt=0)
    expected_yield_quintal_ha: float = Field(ge=0)
    cultivation_cost_inr_ha: float = Field(ge=0)
    transport_cost_inr_per_quintal: float = Field(0, ge=0)
    market_name: str
    price_date: date
    price_source_url: str | None = None
    yield_source_url: str | None = None
    cost_source_url: str | None = None
    data_kind: Literal["observed", "user_reported", "modelled"] = "user_reported"

class FarmField(BaseModel):
    region_id: str = "devanahalli"
    lat: float = Field(13.25, ge=-90, le=90)
    lon: float = Field(77.71, ge=-180, le=180)
    soil_type: str | None = None
    slope_degrees: float | None = Field(None, ge=0, le=90)
    water_access: Literal["rainfed", "irrigated", "unknown"] = "unknown"
    current_crop_id: str | None = None
    selected_variety: str | None = None
    sowing_date: date | None = None
    # These are per-crop observations, not fixed species traits.
    cover_management_c_by_crop: dict[str, SourceValue] = Field(default_factory=dict)
    residue_dry_t_ha_by_crop: dict[str, SourceValue] = Field(default_factory=dict)
    residue_retained_fraction: float | None = Field(None, ge=0, le=1)
    market_by_crop: dict[str, MarketObservation] = Field(default_factory=dict)
    phenology_override_days: dict[str, int] | None = None
    phenology_override_source: str | None = None

class RecommendRequest(BaseModel):
    field: FarmField = Field(default_factory=FarmField)
    priorities: Priorities = Field(default_factory=Priorities)
    climate: Climate = Field(default_factory=Climate)
    as_of: date | None = None

class CriterionScore(BaseModel):
    value: float | None = Field(None, ge=0, le=100)
    method: str
    evidence_urls: list[str] = Field(default_factory=list)
    proxy: bool = False
    reason: str
    input_summary: dict[str, float | str | None] = Field(default_factory=dict)

class CropScore(BaseModel):
    crop_id: str
    subscores: dict[str, CriterionScore]
    total: float | None = Field(None, ge=0, le=100)
    scored_weight_fraction: float = Field(0, ge=0, le=1)
    qualification: str = "provisional"

class Evidence(BaseModel):
    benefits: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    data_used: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"
    confidence_explanation: str = ""
    needs_local_review: bool = True

class Strategy(BaseModel):
    id: str
    name: str
    rank: int
    primary_crop_id: str
    rationale: str
    score: CropScore
    evidence: Evidence
    status: str = "screening_only_not_planting_advice"

class Recommendation(BaseModel):
    location: FarmField
    priorities: Priorities
    strategies: list[Strategy]
    candidate_scores: list[CropScore]
    evidence: Evidence
    methodology: str

class HistoricalYear(BaseModel):
    year: int = Field(ge=1900, le=2200)
    climate: Climate

class SimRequest(BaseModel):
    recommendation: RecommendRequest
    historical_years: list[HistoricalYear] = Field(default_factory=list)
    rain_multiplier: float = Field(1, ge=0, le=3)
    temperature_delta_c: float = Field(0, ge=-15, le=15)
    alert_threshold_score: float = Field(50, ge=0, le=100)
    # Only use actual sourced thresholds; crop-specific thermal response is not calibrated.
    heat_threshold_c_by_crop: dict[str,float] = Field(default_factory=dict)

class Band(BaseModel):
    low_p10: float
    median_p50: float
    high_p90: float
    n_years: int

class SimResult(BaseModel):
    crop_id: str | None
    band: Band | None = None
    threshold_score: float
    below_threshold_years: int | None = None
    by_year: dict[int, float] = Field(default_factory=dict)
    heat_flag_days_by_year: dict[int, int] = Field(default_factory=dict)
    evidence: Evidence
    status: str

class StatusResult(BaseModel):
    region_id: str
    crop_id: str | None
    phase: str
    phase_evidence: str
    vulnerabilities: list[dict]
    bare_field_periods: list[dict]
    evidence: Evidence
