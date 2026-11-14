
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_supabase_user
from app.models.farm import Farm
from app.services.nasa_data_service import get_nasa_farm_data

router = APIRouter(
    prefix="/api/nasa-data",
    tags=["NASA Environmental Data"],
)


@router.get("/farm/{farm_id}")
def get_farm_environmental_data(
    farm_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_supabase_user),
):
    farm = (
        db.query(Farm)
        .filter(
            Farm.id == farm_id,
            Farm.supabase_user_id == user["id"],
        )
        .first()
    )

    if farm is None:
        raise HTTPException(
            status_code=404,
            detail="Farm not found or you do not have access to it.",
        )

    try:
        return get_nasa_farm_data(
            latitude=farm.latitude,
            longitude=farm.longitude,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve NASA environmental data: {exc}",
        ) from exc
