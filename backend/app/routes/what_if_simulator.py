from fastapi import APIRouter

# Reserved for future server-side scenario analysis and dataset integrations.
# Currently, What-if Simulator scenarios are computed client-side.
router = APIRouter(prefix="/api/what-if-simulator", tags=["What-if Simulator"])
