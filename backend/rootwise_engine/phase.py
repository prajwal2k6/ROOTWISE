"""Five crop-cycle stage card. Only documented or observed boundaries are accepted."""
from datetime import date
from .models import Crop

STAGES=('sowing','vegetative','flowering','grain_fill','harvest')

def current_phase(crop: Crop, sowing_date: date, today: date,
                  *, observed_boundaries: dict[str,int] | None = None, source_url: str | None = None) -> dict:
    days=(today-sowing_date).days
    if days<0:
        return {'phase':'not_sown','days_after_sowing':days,'confidence':'high','reason':'Sowing date is in the future'}
    if days==0:
        return {'phase':'sowing','days_after_sowing':0,'confidence':'high','reason':'Recorded sowing date'}
    bounds=observed_boundaries or crop.phenology_days
    if not bounds:
        return {'phase':'unknown','days_after_sowing':days,'confidence':'low','reason':'Missing verified five-stage crop calendar. FAO Kc stages are not botanical phases.'}
    if any(k not in bounds for k in STAGES):
        raise ValueError('Missing required five-stage phase boundaries')
    b=[bounds[k] for k in STAGES]
    if b[0]!=0 or any(x>=y for x,y in zip(b,b[1:])):
        raise ValueError('Invalid five-stage phase boundaries')
    phase='post_harvest' if days>b[-1] else 'sowing'
    if days<=b[-1]:
        for k in STAGES:
            if days>=bounds[k]:phase=k
    return {'phase':phase,'days_after_sowing':days,
            'confidence':'medium' if observed_boundaries else 'medium',
            'reason':'Documented crop stage days' if not observed_boundaries else 'Field-observed stage day offsets',
            'source_url':source_url if observed_boundaries else crop.phenology_source_url}
