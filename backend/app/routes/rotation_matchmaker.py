from fastapi import APIRouter

# Reserved for future server-side calculation and dataset integrations.
# Currently, Rotation Matchmaker decision support is computed client-side.
router = APIRouter(prefix="/api/rotation-matchmaker", tags=["Rotation Matchmaker"])
