"""Public M3 entrypoints. Request/response models are stable Pydantic contracts."""
from datetime import date
from .models import RecommendRequest, Recommendation, SimRequest, StatusResult, Evidence
from .data_loader import load_crops, load_criteria, load_glossary
from .strategies import build_strategies
from .simulate import simulate as _simulate
from .evidence import overall_evidence
from .phase import current_phase
from .vulnerability import vulnerability_windows, bare_field_periods

def recommend(request:RecommendRequest | dict)->Recommendation:
    req=request if isinstance(request,RecommendRequest) else RecommendRequest.model_validate(request)
    crops=load_crops()
    strategies,scores=build_strategies(crops,req.priorities,req.climate,req.field.sowing_date,
                                       req.field,req.as_of)
    return Recommendation(location=req.field,priorities=req.priorities,strategies=strategies,
         candidate_scores=scores,evidence=overall_evidence([s.evidence for s in strategies]),
         methodology=('Six reviewable weighted screening criteria; NULL means unavailable (never imputed), '
                      'rank is a provisional lower-bound policy score, not predicted success. '
                      'Published crop references and location-derived measurements are distinguished by source.'))

def simulate(request:SimRequest | dict):
    req=request if isinstance(request,SimRequest) else SimRequest.model_validate(request)
    return _simulate(req)

def field_status(request:RecommendRequest | dict,*,heat_threshold_c:float|None=None,
                 moisture_threshold_m3m3:float|None=None)->StatusResult:
    req=request if isinstance(request,RecommendRequest) else RecommendRequest.model_validate(request)
    crop=next((c for c in load_crops() if c.id==req.field.current_crop_id),None)
    phase={'phase':'unknown','reason':'No known crop and sowing date'}
    if crop is not None and req.field.sowing_date is not None:
        phase=current_phase(crop,req.field.sowing_date,req.as_of or date.today(),
                            observed_boundaries=req.field.phenology_override_days,
                            source_url=req.field.phenology_override_source)
    vulnerabilities=(vulnerability_windows(crop,req.field.sowing_date,req.climate,
                    heat_threshold_c=heat_threshold_c,
                    moisture_threshold_m3m3=moisture_threshold_m3m3,
                    phenology_days=req.field.phenology_override_days) if crop is not None else [])
    bare=bare_field_periods(crop,req.field.sowing_date,climate=req.climate) if crop else []
    missing=[]
    if phase['phase']=='unknown':missing.append('Five sourced growth-stage boundaries')
    if not req.climate.daily:missing.append('Daily sourced climate/cover observations')
    if heat_threshold_c is None:missing.append('Crop heat threshold and source')
    if moisture_threshold_m3m3 is None:missing.append('Calibrated moisture threshold and source')
    if not bare:missing.append('Observed bare-soil dates (no assumed bare field)')
    return StatusResult(region_id=req.field.region_id,crop_id=req.field.current_crop_id,
                        phase=phase['phase'],phase_evidence=phase['reason'],vulnerabilities=vulnerabilities,
                        bare_field_periods=bare,evidence=Evidence(
            data_used=['Field supplied phase days' if req.field.phenology_override_days else 'Crop database phenology'],
            missing_information=missing,source_urls=[u for u in (req.climate.source_url,req.field.phenology_override_source) if u],
            risks=['Threshold flags are not crop-loss estimates; bare periods require observed cover data'],
            confidence='low',confidence_explanation='No agronomic yield-risk calibration',needs_local_review=True))
