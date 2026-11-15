
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.database import engine


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "application": "ROOTWISE",
            "status": "healthy",
            "database": "connected"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "application": "ROOTWISE",
                "status": "unhealthy",
                "database": "disconnected"
            }
        )
