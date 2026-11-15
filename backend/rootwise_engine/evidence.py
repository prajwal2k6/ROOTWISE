"""Per-crop and overall explanations with explicit unknowns and qualification."""
from .models import Crop, CropScore, Climate, Evidence, FarmField, CRITERIA

def crop_evidence(crop:Crop,score:CropScore,climate:Climate,field:FarmField|None=None)->Evidence:
    field=field or FarmField()
    missing=[k for k in CRITERIA if score.subscores[k].value is None]
    if crop.phenology_days is None and not field.phenology_override_days:
        missing.append('verified variety-specific five-stage phenology')
    if climate.data_kind=='missing':missing.append('site-specific NASA/M2 climate series')
    if crop.water_need.low is None:missing.append('species-specific seasonal crop ET benchmark')
    elif crop.water_need.proxy:missing.append('species-specific water value: FAO category proxy used')
    if not climate.daily:missing.append('daily field temperature/moisture for stage vulnerability')
    if not field.market_by_crop.get(crop.id):missing.append('dated local APMC prices, yield and cultivation costs')
    benefits=[]
    if crop.nitrogen_fixing:benefits.append('Biological N fixation is possible; net soil N gain unquantified')
    if crop.forage_crude_protein_pct_dm.value is not None:
        benefits.append('Published feed crude-protein analysis for a specified material')
    if crop.water_need.low is not None:benefits.append('Published seasonal crop ET reference or category proxy')
    risks=['Scores are an evidence-constrained policy index, not crop yield forecasts or planting advice']
    if score.scored_weight_fraction<0.99999:
        risks.append('Partial priority-weight coverage: missing criteria can change rankings')
    if any(s.proxy for s in score.subscores.values() if s.value is not None):
        risks.append('One or more values are quality proxies or policy indices, not field measurements')
    if climate.data_kind=='missing':risks.append('Location-level feasibility has not been tested')
    urls=sorted({u for u in crop.source_urls+[climate.source_url] if u})
    for s in score.subscores.values():urls.extend(s.evidence_urls)
    urls=sorted(set(urls))
    coverage=score.scored_weight_fraction
    # Coverage and input-source quality; NOT a statistical success probability.
    # High is deliberately withheld unless the agricultural validation step exists.
    conf='medium' if (coverage>=0.75 and climate.source_url and climate.data_kind in ('observed','modelled')
                      and crop.phenology_days is not None) else 'low'
    return Evidence(benefits=benefits,risks=risks,
        data_used=[f'{key}: {s.method}' for key,s in score.subscores.items() if s.value is not None],
        missing_information=missing,source_urls=urls,confidence=conf,
        confidence_explanation=f'Weighted criterion evidence coverage {coverage:.1%}; not a probability of yield/success',
        needs_local_review=True)

def overall_evidence(items:list[Evidence])->Evidence:
    return Evidence(benefits=['Research-backed partial crop screening available'],
       risks=['Crop and market suitability require agronomic validation and field data'],
       data_used=sorted(set(v for e in items for v in e.data_used)),
       missing_information=sorted(set(v for e in items for v in e.missing_information)),
       source_urls=sorted(set(v for e in items for v in e.source_urls)),
       confidence='low',confidence_explanation='Combined criteria and environmental data are incomplete',
       needs_local_review=True)
