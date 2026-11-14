from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models.farm import Farm
from app.routes.rotation_matchmaker import router as rotation_matchmaker_router
from app.routes.farms import router as farms_router
from app.routes.nasa_data import router as nasa_data_router



app = FastAPI(
    title="ROOTWISE API",
    description="Agricultural Intelligence and Crop Rotation Platform",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
],    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create missing database tables.
@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


app.include_router(farms_router)
app.include_router(rotation_matchmaker_router)
app.include_router(nasa_data_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to ROOTWISE API",
        "status": "Backend is running successfully!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "ROOTWISE"
    }