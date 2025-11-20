"""FastAPI weather data API with endpoints for storage and retrieval."""

from __future__ import annotations

import sys
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import get_db

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
    title="Weather API",
    description="API for storing and retrieving weather data from the OpenWeather pipeline",
    version="0.1.0",
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
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Dictionary with status and service name
    """
    return {"status": "healthy", "service": "weather-api"}


@app.post("/api/weather", response_model=schemas.WeatherRecordResponse, status_code=201)
async def create_weather_record(
    weather_data: dict[str, Any], db: Session = Depends(get_db)
) -> schemas.WeatherRecordResponse:
    """
    Create a new weather record.

    Accepts weather data from the consumer and stores it in the database.
    Uses upsert pattern to prevent duplicate records.

    Args:
        weather_data: Weather observation with location and current conditions
        db: Database session

    Returns:
        Created or updated WeatherRecord

    Raises:
        HTTPException: 400 if data is malformed, 500 for database errors
    """
    try:
        logger.info("Received weather data")
        logger.debug(f"Weather data: {weather_data}")

        record = crud.create_weather_record(db, weather_data)
        logger.success(f"Weather record processed: ID={record.id}")
        return record

    except KeyError as key_error:
        logger.error(f"Missing required field in weather data: {key_error}")
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(key_error)}")
    except ValueError as value_error:
        logger.error(f"Invalid data format in weather record: {value_error}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(value_error)}")
    except Exception as database_error:
        logger.error(f"Database error creating weather record: {database_error}")
        raise HTTPException(
            status_code=500, detail="Failed to create weather record. Please try again."
        )


@app.get("/api/weather", response_model=schemas.WeatherRecordList)
async def list_weather_records(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page (default 20)"),
    db: Session = Depends(get_db),
) -> schemas.WeatherRecordList:
    """
    List all weather records with pagination.

    Returns weather records ordered by creation time (newest first).

    Args:
        page: Page number (1-indexed)
        page_size: Number of records per page (default 20, max 100)
        db: Database session

    Returns:
        Paginated list of WeatherRecords with total count
    """
    skip = (page - 1) * page_size
    records, total = crud.get_weather_records(db, skip=skip, limit=page_size)

    return {"total": total, "page": page, "page_size": page_size, "records": records}


@app.get("/api/weather/{record_id}", response_model=schemas.WeatherRecordResponse)
async def get_weather_record(
    record_id: int, db: Session = Depends(get_db)
) -> schemas.WeatherRecordResponse:
    """
    Get a specific weather record by ID.

    Args:
        record_id: ID of the weather record
        db: Database session

    Returns:
        WeatherRecord

    Raises:
        HTTPException: 404 if record not found
    """
    record = crud.get_weather_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return record


@app.get("/api/weather/location/{location_name}", response_model=schemas.WeatherRecordList)
async def get_weather_by_location(
    location_name: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page (default 20)"),
    db: Session = Depends(get_db),
) -> schemas.WeatherRecordList:
    """
    Get weather records for a location by partial name match (case-insensitive).

    Searches for locations whose name contains the search term.
    Results are ordered by creation time (newest first).

    Args:
        location_name: Partial location name to search for
        page: Page number (1-indexed)
        page_size: Number of records per page (default 20, max 100)
        db: Database session

    Returns:
        Paginated list of WeatherRecords for the location

    Raises:
        HTTPException: 404 if no records found
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
async def get_latest_weather(
    location_name: str, db: Session = Depends(get_db)
) -> schemas.WeatherRecordResponse:
    """
    Get the most recent weather record for a location.

    Searches for locations whose name contains the search term
    (case-insensitive partial match).

    Args:
        location_name: Partial location name to search for
        db: Database session

    Returns:
        Most recent WeatherRecord for the location

    Raises:
        HTTPException: 404 if no records found
    """
    record = crud.get_latest_weather_by_location(db, location_name)
    if not record:
        raise HTTPException(
            status_code=404, detail=f"No weather records found for location: {location_name}"
        )
    return record


if __name__ == "__main__":
    import uvicorn

    from .config import settings

    uvicorn.run("api_app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
