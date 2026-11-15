"""FAO simplified four-stage Kc × observed/modelled ET0 calculator.

Kc values and example four-stage lengths originate from FAO Crop Water Needs.
The stage lengths in the included data are GENERIC reference examples and
must not be described as verified biological phenology of a local variety.
"""
from datetime import date, timedelta
from .models import Crop, Climate


def seasonal_etc_from_daily_et0(crop: Crop, sowing_date: date, climate: Climate) -> dict:
    """ETc = sum(Kc_stage × ET0_day), only with complete ET0 daily coverage.

    This computes reference crop evapotranspiration, *not irrigation need*.
    Missing days => no numeric result. Crop production and stress corrections
    are outside the scope of this simplified four-stage FAO reference.
    """
    stages = ('initial', 'development', 'mid', 'late')
    if not crop.fao_stage_lengths or not crop.kc:
        return {'etc_mm': None, 'reason': 'No documented FAO reference water-use stage lengths'}
    if any(k not in crop.kc for k in stages):
        return {'etc_mm': None, 'reason': 'Incomplete FAO stage Kc reference'}
    et0_by_day = {x.date: x.et0_mm for x in climate.daily if x.et0_mm is not None}
    offset = 0
    total = 0.0
    for stage, duration in zip(stages, crop.fao_stage_lengths):
        for i in range(duration):
            day = sowing_date + timedelta(days=offset+i)
            et0 = et0_by_day.get(day)
            if et0 is None:
                return {'etc_mm': None, 'reason': f'No daily ET0 on {day.isoformat()}; full season required'}
            total += crop.kc[stage] * et0
        offset += duration
    return {
        'etc_mm': round(total, 3),
        'unit': 'mm per FAO reference growing period',
        'days': offset,
        'method': 'sum_over_days(Kc_stage * ET0_day)',
        'source_url': crop.kc_source_url,
        'proxy': crop.kc_proxy or crop.water_need.proxy,
        'note': 'Generic FAO stage lengths; NOT cultivar-specific phenology or irrigation need',
    }
