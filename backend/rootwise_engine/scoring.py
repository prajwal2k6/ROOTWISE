"""Six reproducible screening criteria with explicit evidence and missingness.

NOT a trained agronomic yield model. Normalization targets are ROOTWISE policy
choices, *not* values asserted by FAO or observations for Devanahalli.
"""
from __future__ import annotations
from datetime import date
from .models import Crop, CropScore, CriterionScore, Priorities, Climate, FarmField, CRITERIA
from .water import seasonal_etc_from_daily_et0

# Explicit, reviewable model targets. Change these in a versioned decision-policy review,
# not to make one crop rank higher than another.
FORAGE_PROTEIN_TARGET_PCT_DM = 20.0  # CP benchmark for quality-only index; not a feed ration standard
RESIDUE_RETAINED_TARGET_T_DM_HA = 5.0  # comparator for retained dry biomass, not SOC sequestration
MARKET_RETURN_ON_COST_TARGET = 1.0  # ROI=100% saturates market score; user-defined policy
MAX_MARKET_PRICE_AGE_DAYS = 90       # freshness rule; price not a long-term crop trait
FAO_GENERAL = 'https://www.fao.org/4/s2022e/s2022e07.htm'
RUSLE_SOURCE = 'https://www.fao.org/land-water/land/land-governance-and-planning/land-resources-planning-toolbox/detail/revised-universal-soil-loss-equation/en'


def _clip(x: float) -> float:
    return round(max(0.0, min(100.0, x)), 3)


def _available(score: float, method: str, reason: str, urls=None, *, proxy=False, inputs=None):
    return CriterionScore(value=_clip(score), method=method, reason=reason,
                          evidence_urls=list(dict.fromkeys(x for x in (urls or []) if x)),
                          proxy=proxy, input_summary=inputs or {})


def _missing(reason: str):
    return CriterionScore(value=None, method='unavailable', reason=reason)


def score_crop(crop: Crop, priorities: Priorities, climate: Climate | None = None,
               crops: list[Crop] | None = None, sowing_date: date | None = None,
               field: FarmField | None = None, as_of: date | None = None) -> CropScore:
    climate = climate or Climate()
    field = field or FarmField()
    as_of = as_of or date.today()
    candidates = crops or [crop]
    subs = {k: _missing('Insufficient traceable evidence/inputs for this criterion') for k in CRITERIA}

    # WATER: relative published seasonal ET demand proxy for comparisons, never
    # claim field water sufficiency without a crop ETc and independently supplied water.
    mids = [(c.water_need.low+c.water_need.high)/2 for c in candidates
            if c.water_need.low is not None and c.water_need.high is not None]
    if mids and crop.water_need.low is not None and crop.water_need.high is not None:
        x=(crop.water_need.low+crop.water_need.high)/2
        lo,hi=min(mids),max(mids)
        v=100. if lo==hi else 100*(hi-x)/(hi-lo)
        subs['water_use']=_available(v,'relative_inverse_FAO_seasonal_ET_reference',
            'Comparative demand index only; NOT sufficiency, yield, or irrigation need',
            [crop.water_need.source_url],proxy=crop.water_need.proxy,
            inputs={'seasonal_reference_mid_mm':x})
    crop_etc=climate.seasonal_etc_by_crop_mm.get(crop.id)
    etc_method='M2_supplied_seasonal_ETc'
    if crop_etc is None and sowing_date and climate.daily:
        estimate=seasonal_etc_from_daily_et0(crop,sowing_date,climate)
        crop_etc=estimate.get('etc_mm')
        etc_method='daily_Kc_times_ET0_FAO_reference_stage_lengths'
    if crop_etc is None and len(candidates)==1:  # legacy one-crop use only
        crop_etc=climate.seasonal_etc_mm
    if (climate.data_kind in ('observed','modelled') and climate.source_url
        and crop_etc is not None and crop_etc>0
        and climate.seasonal_effective_rainfall_mm is not None
        and climate.seasonal_irrigation_mm is not None):
        supply=climate.seasonal_effective_rainfall_mm+climate.seasonal_irrigation_mm
        subs['water_use']=_available(100*min(1,supply/crop_etc),'water_supply_over_crop_ETc_capped',
            'First-pass seasonal balance only: timing, infiltration, runoff and root-zone storage unmodelled',
            [climate.source_url,crop.kc_source_url],proxy=(crop.water_need.proxy or 'reference' in climate.source_id.lower()) if climate.source_id else crop.water_need.proxy,
            inputs={'modelled_effective_rain_mm':climate.seasonal_effective_rainfall_mm,
                    'irrigation_mm':climate.seasonal_irrigation_mm,'crop_etc_mm':crop_etc,
                    'etc_method':etc_method})

    # FORAGE: published CP for a named forage material. This is a PROTEIN-QUALITY
    # indicator, not dry matter yield, total forage amount or animal diet suitability.
    cp=crop.forage_crude_protein_pct_dm
    if cp.value is not None and 0<=cp.value<=100 and cp.source_url:
        subs['forage_value']=_available(100*cp.value/FORAGE_PROTEIN_TARGET_PCT_DM,
            'forage_crude_protein_quality_proxy',
            'Feedipedia feed-material CP reference: quality only, no forage availability; crop materials differ',
            [cp.source_url],proxy=True,
            inputs={'crude_protein_pct_dm':cp.value,'benchmark_pct_dm':FORAGE_PROTEIN_TARGET_PCT_DM,
                    'material':crop.forage_material or 'unspecified'})

    # N: yes/no biological capacity, explicitly NOT net soil nitrogen credit.
    subs['nitrogen_fixing']=_available(100 if crop.nitrogen_fixing else 0,
        'binary_biological_nitrogen_fixing_capability',
        'Biological capability only. Fixation amount, harvest N removal and N soil credit unknown',
        crop.source_urls,inputs={'can_fix_nitrogen':str(crop.nitrogen_fixing).lower()})

    # EROSION: FAO RUSLE A=R*K*LS*C*P. Only C varies in this bounded comparison.
    # Do not invent crop C-factors; require calibrated field/crop cover-management data.
    c_input=field.cover_management_c_by_crop.get(crop.id)
    if c_input and c_input.value is not None and 0<=c_input.value<=1:
        if c_input.kind in ('user_reported','field_measurement') or c_input.source_url:
            subs['erosion_reduction']=_available(100*(1-c_input.value),
                'RUSLE_relative_cover_factor_vs_bare_soil',
                'Only RUSLE C-factor comparison (C_bare=1); NOT predicted soil loss; R,K,LS,P still required',
                [RUSLE_SOURCE,c_input.source_url],proxy=c_input.proxy or c_input.kind=='user_reported',
                inputs={'cover_management_factor_C':c_input.value,'reference_bare_C':1.0})

    # ORGANIC MATTER: retained biomass INPUT proxy. Not SOC increase or sequestration.
    biomass=field.residue_dry_t_ha_by_crop.get(crop.id)
    fraction=field.residue_retained_fraction
    if fraction is not None and fraction == 0:
        subs['organic_matter']=_available(0,'retained_residue_dry_biomass_benchmark',
            'Farmer reports all crop residues removed; zero above-ground residue returned via this pathway',
            proxy=True,inputs={'retained_fraction':0.0,'retained_t_dm_ha':0.0})
    elif (biomass and fraction is not None and biomass.value is not None and biomass.value>=0
          and (biomass.kind in ('field_measurement','user_reported') or biomass.source_url)):
        retained=biomass.value*fraction
        subs['organic_matter']=_available(100*retained/RESIDUE_RETAINED_TARGET_T_DM_HA,
            'retained_residue_dry_biomass_benchmark',
            'Dry residue returned to soil relative to a stated project target. Not a soil organic carbon change.',
            [biomass.source_url],proxy=True,
            inputs={'residue_dry_t_dm_ha':biomass.value,'retained_fraction':fraction,
                    'retained_t_dm_ha':round(retained,3),'target_t_dm_ha':RESIDUE_RETAINED_TARGET_T_DM_HA})

    # MARKET: dated crop price and yield and full variable input estimates.
    # Net margin / cost with saturation at project-defined ROI benchmark.
    market=field.market_by_crop.get(crop.id)
    if market is not None:
        age=(as_of-market.price_date).days
        if 0<=age<=MAX_MARKET_PRICE_AGE_DAYS:
            revenue=market.price_inr_per_quintal*market.expected_yield_quintal_ha
            total_cost=market.cultivation_cost_inr_ha + market.transport_cost_inr_per_quintal*market.expected_yield_quintal_ha
            if total_cost>0:
                margin=revenue-total_cost
                roi=margin/total_cost
                subs['market_suitability']=_available(100*roi/MARKET_RETURN_ON_COST_TARGET,
                    'net_return_on_cost_policy_index',
                    'Market indicator from dated price, yield and cost inputs; ROI target is Rootwise policy, not forecast certainty',
                    [market.price_source_url,market.yield_source_url,market.cost_source_url],
                    proxy=market.data_kind!='observed',inputs={'gross_inr_ha':round(revenue,2),
                    'cost_inr_ha':round(total_cost,2),'net_inr_ha':round(margin,2),
                    'roi':round(roi,4),'market':market.market_name,'price_date':market.price_date.isoformat()})
    weights=priorities.weights()
    available=[k for k in CRITERIA if subs[k].value is not None and weights[k]>0]
    coverage=sum(weights[k] for k in available)
    lower_bound=sum(weights[k]*subs[k].value for k in available) if coverage else None
    qualification='no_active_criteria' if not any(weights.values()) else (
        'no_supported_scores' if lower_bound is None else
        'conservative_known_contribution_not_crop_suitability' if coverage<0.99999 else
        'all_criteria_scored_not_validated_suitability')
    return CropScore(crop_id=crop.id,subscores=subs,total=round(lower_bound,3) if lower_bound is not None else None,
                     scored_weight_fraction=round(coverage,5),qualification=qualification)
