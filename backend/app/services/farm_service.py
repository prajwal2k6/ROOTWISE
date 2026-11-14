from sqlalchemy.orm import Session
from app.models.farm import Farm
from app.schemas.farm import FarmCreate


def create_farm(db: Session, user_id: str, farm_data: FarmCreate) -> Farm:
    farm = Farm(
        supabase_user_id=user_id,
        farm_name=farm_data.farm_name,
        latitude=farm_data.latitude,
        longitude=farm_data.longitude,
        boundary=farm_data.boundary,
        area_acres=farm_data.area_acres,
        area_hectares=farm_data.area_hectares,
        soil_type=farm_data.soil_type,
        irrigation=farm_data.irrigation,
        main_crop=farm_data.main_crop,
        other_crops=farm_data.other_crops,
        sowing_season=farm_data.sowing_season,
        harvest_period=farm_data.harvest_period,
        previous_crop_sequence=farm_data.previous_crop_sequence,
        crop_frequency=farm_data.crop_frequency,
        priority=farm_data.priority,
        notes=farm_data.notes,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def get_farms_by_user(db: Session, user_id: str) -> list[Farm]:
    return (
        db.query(Farm)
        .filter(Farm.supabase_user_id == user_id)
        .order_by(Farm.created_at.desc())
        .all()
    )
