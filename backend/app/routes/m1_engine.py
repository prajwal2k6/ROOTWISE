from fastapi import APIRouter

from rootwise_engine.api import recommend, simulate
from rootwise_engine.models import RecommendRequest, SimRequest

router = APIRouter(prefix="/api/m1", tags=["M1 Recommendation Engine"])


@router.post("/recommend")
def create_recommendations(request: RecommendRequest):
    """Run M1 with caller-supplied, validated field and climate observations."""
    return recommend(request).model_dump(mode="json")


@router.post("/simulate")
def create_simulation(request: SimRequest):
    """Run M1's crop scenario simulation with the supplied evidence inputs."""
    return simulate(request)
