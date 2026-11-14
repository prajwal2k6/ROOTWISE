from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_supabase_user
from app.schemas.farm import FarmCreate, FarmResponse
from app.services import farm_service

router = APIRouter(prefix="/api/farms", tags=["Farms"])


@router.post("/", response_model=FarmResponse, status_code=201)
def create_farm(
    farm_data: FarmCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_supabase_user),
):
    for point in farm_data.boundary:
        if len(point) != 2:
            raise HTTPException(
                status_code=400,
                detail="Each boundary point needs longitude and latitude.",
            )

        longitude, latitude = point

        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise HTTPException(
                status_code=400,
                detail="Invalid boundary coordinates.",
            )

    return farm_service.create_farm(db, user_id=user["id"], farm_data=farm_data)


@router.get("/", response_model=list[FarmResponse])
def get_my_farms(
    db: Session = Depends(get_db),
    user: dict = Depends(get_supabase_user),
):
    return farm_service.get_farms_by_user(db, user_id=user["id"])
