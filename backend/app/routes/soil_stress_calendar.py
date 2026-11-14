from fastapi import APIRouter

# Reserved for future server-side environmental stress calculations.
# Currently, Soil Stress Calendar indicators are presented client-side.
router = APIRouter(prefix="/api/soil-stress-calendar", tags=["Soil Stress Calendar"])
