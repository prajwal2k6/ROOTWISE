"""Historical-year and rainfall what-if simulation: no synthetic NASA observations."""
from __future__ import annotations
import numpy as np
from .models import SimRequest, SimResult, Band, Evidence
from .data_loader import load_crops
from .scoring import score_crop

def simulate(request:SimRequest)->list[SimResult]:
    crops=load_crops(); p=request.recommendation.priorities
    base_field=request.recommendation.field
    output=[]
    for crop in crops:
        by_year={}; heat_by_year={}; urls=[]
        for row in request.historical_years:
            climate=row.climate.model_copy(deep=True)
            # Rain multiplier is a WHAT-IF applied to modelled EFFECTIVE rain,
            # not a mutation of the NASA underlying observations.
            if climate.seasonal_effective_rainfall_mm is not None:
                climate.seasonal_effective_rainfall_mm*=request.rain_multiplier
            required=(crop.id in climate.seasonal_etc_by_crop_mm
                      and climate.seasonal_effective_rainfall_mm is not None
                      and climate.seasonal_irrigation_mm is not None
                      and bool(climate.source_url) and climate.data_kind in ('modelled','observed'))
            if not required:continue
            score=score_crop(crop,p,climate,crops,base_field.sowing_date,base_field,
                             request.recommendation.as_of)
            if score.total is None or score.subscores['water_use'].value is None:continue
            by_year[row.year]=score.total
            if climate.source_url:urls.append(climate.source_url)
            # Optional auditable threshold flags. Not a calibrated yield-score change.
            threshold=request.heat_threshold_c_by_crop.get(crop.id)
            if threshold is not None and climate.daily:
                heat_by_year[row.year]=sum(1 for d in climate.daily if d.tmax_c is not None
                                           and d.tmax_c+request.temperature_delta_c>threshold)
        band=None; below=None
        if len(by_year)>=3:
            pct=np.percentile(list(by_year.values()),[10,50,90]).tolist()
            band=Band(low_p10=round(pct[0],3),median_p50=round(pct[1],3),
                      high_p90=round(pct[2],3),n_years=len(by_year))
            below=sum(x<request.alert_threshold_score for x in by_year.values())
        missing=[]
        if band is None:missing.append('3+ sourced historical years with crop-specific ETc, effective rain, irrigation')
        if request.temperature_delta_c!=0 and not heat_by_year:
            missing.append('Heat-risk count needs daily Tmax and an independently sourced crop threshold')
        if request.temperature_delta_c!=0:
            missing.append('temperature slider does not change scores; no validated temperature-yield coefficient')
        ev=Evidence(benefits=['Sourced historical rainfall/ETc scenario comparison'] if band else [],
          risks=['Partial score is not a historical yield or success distribution',
                 'Historical years may combine crop-stage-incompatible season windows'],
          data_used=['Scored year-level climate input; per-crop water adequacy'] if band else [],
          missing_information=missing,source_urls=sorted(set(urls)),confidence='low',
          confidence_explanation='Nonvalidated screening score percentiles, not a probabilistic forecast',
          needs_local_review=True)
        output.append(SimResult(crop_id=crop.id,band=band,threshold_score=request.alert_threshold_score,
                                below_threshold_years=below,by_year=by_year,heat_flag_days_by_year=heat_by_year,
                                evidence=ev,status='provisional_historical_screening' if band else 'insufficient_historical_data'))
    return output
