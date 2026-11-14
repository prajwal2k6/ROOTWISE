from fastapi import APIRouter

# Reserved for aggregated farm metrics and summary views.
# Currently, farm data and workspace views are organized client-side.
router = APIRouter(prefix="/api/farmer-dashboard", tags=["Farmer Dashboard"])
