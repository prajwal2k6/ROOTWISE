from fastapi import APIRouter

# Reserved for future uncertainty estimation and provenance indicators.
# Currently, Evidence & Confidence details are presented client-side.
router = APIRouter(prefix="/api/evidence-confidence", tags=["Evidence & Confidence"])
