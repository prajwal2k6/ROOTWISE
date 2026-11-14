from fastapi import APIRouter

# Reserved for future satellite Earth observation time-series queries.
# Currently, Land Memory observations are presented client-side.
router = APIRouter(prefix="/api/land-memory", tags=["Land Memory"])
