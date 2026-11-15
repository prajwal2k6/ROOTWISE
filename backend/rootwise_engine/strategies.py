"""Three distinct *screening* strategies; never claim a rotation without rotation data."""
from __future__ import annotations
from datetime import date
from .models import Crop, CropScore, Priorities, Climate, FarmField, Strategy
from .scoring import score_crop
from .evidence import crop_evidence

# Intentional policy alternatives; scores displayed to the user always use the
# user's original weights, not these temporary selection-time weights.
FOCUSES = [
    ('water_focus','Water-conserving option', {'water_use':3.0,'nitrogen_fixing':0.5}),
    ('soil_focus','Soil and nitrogen option',{'nitrogen_fixing':3.0,'erosion_reduction':2.0,'organic_matter':2.0}),
    ('balanced_focus','Farmer-priority balanced option',{}),
]

def _adjust_priorities(original:Priorities,focus:dict[str,float]) -> Priorities:
    raw=original.model_dump()
    if focus:
        raw={key:val*focus.get(key,1.0) for key,val in raw.items()}
    maximum=max(raw.values(),default=0)
    if maximum>100:raw={key:100*val/maximum for key,val in raw.items()}
    return Priorities(**raw)

def build_strategies(crops:list[Crop],priorities:Priorities,climate:Climate,
                     sowing_date:date|None=None,field:FarmField|None=None,
                     as_of:date|None=None) -> tuple[list[Strategy],list[CropScore]]:
    field=field or FarmField()
    base=[score_crop(c,priorities,climate,crops,sowing_date,field,as_of) for c in crops]
    by_id={x.crop_id:x for x in base}; by_crop={c.id:c for c in crops}
    chosen=set(); out=[]
    for ident,name,boost in FOCUSES:
        adjusted=_adjust_priorities(priorities,boost)
        options=[]
        for c in crops:
            if c.id in chosen:continue
            candidate=score_crop(c,adjusted,climate,crops,sowing_date,field,as_of)
            if candidate.total is None:continue
            if ident=='water_focus' and candidate.subscores['water_use'].value is None:continue
            if ident=='soil_focus' and candidate.subscores['nitrogen_fixing'].value!=100:continue
            options.append(candidate)
        if not options: # fallback to a distinct scored crop
            options=[by_id[c.id] for c in crops if c.id not in chosen and by_id[c.id].total is not None]
        if not options:continue
        # Tie-break is deterministic, but scientific superiority cannot be inferred.
        candidate=sorted(options,key=lambda x:(-x.total,-x.scored_weight_fraction,x.crop_id))[0]
        chosen.add(candidate.crop_id)
        reported=by_id[candidate.crop_id]
        out.append(Strategy(id=ident,name=name,rank=0,primary_crop_id=candidate.crop_id,
            rationale=('Selected via a focus-specific screen; final score shown uses farmer weights. '
                       'Tied scores are not proof of superiority. No rotation agronomy is claimed.'),
            score=reported,evidence=crop_evidence(by_crop[candidate.crop_id],reported,climate,field)))
    out.sort(key=lambda x:(-(x.score.total if x.score.total is not None else -1),
                           -x.score.scored_weight_fraction,x.primary_crop_id))
    for idx,x in enumerate(out,1):x.rank=idx
    return out,base
