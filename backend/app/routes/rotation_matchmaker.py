
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_supabase_user
from app.models.farm import Farm
from app.services.rotation_matchmaker_service import (
    build_rotation_recommendations,
)

router = APIRouter(
    prefix="/api/rotation-matchmaker",
    tags=["Rotation Matchmaker"],
)


@router.get("/{farm_id}")
def get_rotation_recommendations(
    farm_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_supabase_user),
):
    """
    Generate crop rotation decision-support pathways
    for a farm owned by the authenticated user.
    """

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

    return build_rotation_recommendations(farm)
