from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models.farm import Farm
from app.routes.farms import router as farms_router


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