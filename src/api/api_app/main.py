import sys

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy.orm import Session

from api_app import crud, schemas
from api_app.database import get_db

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

# Create FastAPI app
app = FastAPI(
    title="Weather API", description="API for storing and retrieving weather data", version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "weather-api"}


@app.post("/api/weather", response_model=schemas.WeatherRecordResponse, status_code=201)
async def create_weather_record(weather_data: dict, db: Session = Depends(get_db)):
    """
    Create a new weather record.

    Accepts weather data from the consumer and stores it in the database.
    """
    try:
        logger.info("Received weather data")
        logger.debug(f"Weather data: {weather_data}")

        record = crud.create_weather_record(db, weather_data)
        return record

    except Exception as e:
        logger.error(f"Error creating weather record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create weather record: {str(e)}")


@app.get("/api/weather", response_model=schemas.WeatherRecordList)
async def list_weather_records(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
):
    """
    List weather records with pagination.
    """
    skip = (page - 1) * page_size
    records, total = crud.get_weather_records(db, skip=skip, limit=page_size)

    return {"total": total, "page": page, "page_size": page_size, "records": records}


@app.get("/api/weather/{record_id}", response_model=schemas.WeatherRecordResponse)
async def get_weather_record(record_id: int, db: Session = Depends(get_db)):
    """
    Get a specific weather record by ID.
    """
    record = crud.get_weather_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return record


@app.get("/api/weather/location/{location_name}", response_model=schemas.WeatherRecordList)
async def get_weather_by_location(
    location_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
):
    """
    Get weather records for a specific location.
    """
    skip = (page - 1) * page_size
    records, total = crud.get_weather_by_location(db, location_name, skip=skip, limit=page_size)

    if not records:
        raise HTTPException(
            status_code=404, detail=f"No weather records found for location: {location_name}"
        )

    return {"total": total, "page": page, "page_size": page_size, "records": records}


@app.get(
    "/api/weather/location/{location_name}/latest", response_model=schemas.WeatherRecordResponse
)
async def get_latest_weather(location_name: str, db: Session = Depends(get_db)):
    """
    Get the most recent weather record for a location.
    """
    record = crud.get_latest_weather_by_location(db, location_name)
    if not record:
        raise HTTPException(
            status_code=404, detail=f"No weather records found for location: {location_name}"
        )
    return record


if __name__ == "__main__":
    import uvicorn

    from api_app.config import settings

    uvicorn.run("api_app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
