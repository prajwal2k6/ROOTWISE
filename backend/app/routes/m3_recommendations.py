"""Authenticated M3 recommendation API, scoped to the signed-in farmer."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_verified_supabase_user
from app.database import get_db
from app.models.farmer import Farmer
from app.models.field import Field
from app.schemas.recommendation import RecommendationRequest
from app.services.recommendation_service import (
    build_recommendation_context,
    run_m1_recommendation_engine,
)

router = APIRouter(prefix="/recommendations", tags=["M3 Recommendations"])


@router.post("/")
def generate_field_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_verified_supabase_user),
):
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Account email is required")

    farmer = db.scalar(
        select(Farmer).where(func.lower(Farmer.email) == email.lower())
    )
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    field = db.scalar(
        select(Field).where(
            Field.id == request.field_id,
            Field.farmer_id == farmer.id,
        )
    )
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")

    context = build_recommendation_context(db, field.id)
    return run_m1_recommendation_engine(
        context=context,
        target_season=request.target_season,
        target_year=request.target_year,
    )
