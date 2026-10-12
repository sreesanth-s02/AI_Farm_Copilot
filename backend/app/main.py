from fastapi import FastAPI
from sqlalchemy import text
from app.api.weather import router as weather_router
from app.db.database import engine
from app.api.farmers import router as farmers_router
from app.api.farms import router as farms_router
from app.api.fields import router as fields_router
from app.api.crops import router as crops_router
from app.api.soil import router as soil_router
from app.api.recommendations import router as recommendations_router
app = FastAPI(
    title="AI Farm Copilot API",
    description="Backend API for AI-powered precision agriculture",
    version="1.0.0"
)
app.include_router(farmers_router)
app.include_router(farms_router)
app.include_router(fields_router)
app.include_router(crops_router)
app.include_router(soil_router)
app.include_router(weather_router)
app.include_router(recommendations_router)
@app.get("/")
def root():
    return {
        "message": "AI Farm Copilot API is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "MySQL",
            "status": "connected"
        }

    except Exception as e:
        return {
            "database": "MySQL",
            "status": "error",
            "message": str(e)
        }