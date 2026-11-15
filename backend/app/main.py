from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import Farm, Farmer
from app.routes.rotation_matchmaker import router as rotation_matchmaker_router
from app.routes.farms import router as farms_router
from app.routes.nasa_data import router as nasa_data_router
from app.routes.what_if_simulator import router as what_if_simulator_router
from app.routes.m1_engine import router as m1_engine_router
from app.routes import climate, health, map_data, risk, timeseries
from app.routes.m2_catalog import router as m2_catalog_router
from app.routes.m2_fields import router as m2_fields_router
from app.routes.m3_recommendations import router as m3_recommendations_router

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
    # Legacy tables retain their established startup behavior. M2/M3 tables
    # are created only through the additive Alembic migrations.
    Base.metadata.create_all(
        bind=engine,
        tables=[Farmer.__table__, Farm.__table__],
    )


app.include_router(farms_router)
app.include_router(rotation_matchmaker_router)
app.include_router(nasa_data_router)
app.include_router(what_if_simulator_router)
app.include_router(m1_engine_router)
app.include_router(health.router, prefix="/api/v1")
app.include_router(climate.router, prefix="/api/v1")
app.include_router(map_data.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(timeseries.router, prefix="/api/v1")
app.include_router(m2_catalog_router, prefix="/api/v1")
app.include_router(m2_fields_router, prefix="/api/v1")
app.include_router(m3_recommendations_router, prefix="/api/v1")

# Convenience aliases for /simulate and /api/simulate
@app.post("/simulate")
@app.get("/simulate")
@app.post("/api/simulate")
@app.get("/api/simulate")
def simulate_proxy(
    temperature_delta: float = 0.0,
    rainfall_delta_percent: float = 0.0,
    preset: str = "Normal Year"
):
    from app.routes.what_if_simulator import simulate_scenario, SimulationRequest
    return simulate_scenario(SimulationRequest(
        temperature_delta=temperature_delta,
        rainfall_delta_percent=rainfall_delta_percent,
        preset=preset
    ))



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
