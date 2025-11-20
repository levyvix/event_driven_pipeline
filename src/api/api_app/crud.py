"""Database operations for weather data management."""

from __future__ import annotations

from typing import Any

from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models


def get_or_create_location(db: Session, location_data: dict[str, Any]) -> models.Location:
    """
    Get existing location or create new one.

    Uses exact match on coordinates (lat, lon) to find existing locations.
    This upsert pattern ensures duplicate locations with same coordinates
    are not created.

    Args:
        db: Database session
        location_data: Dictionary with keys: name, region, country, lat, lon, tz_id

    Returns:
        Location object (existing or newly created)
    """
    location: models.Location | None = (
        db.query(models.Location)
        .filter(
            models.Location.lat == location_data["lat"],
            models.Location.lon == location_data["lon"],
        )
        .first()
    )

    if location:
        logger.debug(f"Found existing location: {location.name}, {location.country}")
        return location

    logger.info(f"Creating new location: {location_data['name']}, {location_data['country']}")
    location = models.Location(**location_data)
    db.add(location)
    db.flush()  # Get the ID without committing
    return location


def get_or_create_condition(db: Session, condition_data: dict[str, Any]) -> models.WeatherCondition:
    """
    Get existing weather condition or create new one.

    Uses exact match on condition code to find existing conditions.
    This upsert pattern prevents duplicate condition records.

    Args:
        db: Database session
        condition_data: Dictionary with keys: code, text, icon

    Returns:
        WeatherCondition object (existing or newly created)
    """
    condition: models.WeatherCondition | None = (
        db.query(models.WeatherCondition)
        .filter(models.WeatherCondition.code == condition_data["code"])
        .first()
    )

    if condition:
        logger.debug(f"Found existing condition: {condition.text}")
        return condition

    logger.info(f"Creating new condition: {condition_data['text']}")
    condition = models.WeatherCondition(**condition_data)
    db.add(condition)
    db.flush()
    return condition


def create_weather_record(db: Session, weather_data: dict[str, Any]) -> models.WeatherRecord:
    """
    Create or update a weather record (upsert pattern).

    Extracts location and condition information from the weather data,
    creates or retrieves related entities, then creates or updates the
    weather record based on the composite key (location, condition, timestamp).

    This ensures that duplicate observations (same location, condition, time)
    update the existing record rather than creating a duplicate.

    Args:
        db: Database session
        weather_data: Dictionary with structure:
            {
                "location": {...},
                "current": {
                    "condition": {...},
                    ... other fields ...
                }
            }

    Returns:
        Created or updated WeatherRecord

    Raises:
        KeyError: If required fields are missing from input
        Exception: On database errors (logged and re-raised)
    """
    try:
        # Extract nested data
        location_data_raw: dict[str, Any] = weather_data["location"].copy()
        current_data: dict[str, Any] = weather_data["current"].copy()
        condition_data: dict[str, Any] = current_data.pop("condition")

        # Extract localtime fields from location data (they belong to weather record)
        localtime_epoch: int = location_data_raw.pop("localtime_epoch")
        localtime: str = location_data_raw.pop("localtime")

        # Get or create related entities
        location: models.Location = get_or_create_location(db, location_data_raw)
        condition: models.WeatherCondition = get_or_create_condition(db, condition_data)

        # Check if record already exists (same location, condition, and timestamp)
        existing_record: models.WeatherRecord | None = (
            db.query(models.WeatherRecord)
            .filter(
                models.WeatherRecord.location_id == location.id,
                models.WeatherRecord.condition_id == condition.id,
                models.WeatherRecord.localtime_epoch == localtime_epoch,
            )
            .first()
        )

        if existing_record:
            # Update existing record with new data
            logger.info(f"Updating existing weather record ID: {existing_record.id}")
            for key, value in current_data.items():
                setattr(existing_record, key, value)
            existing_record.localtime = localtime
            db.commit()
            db.refresh(existing_record)
            logger.success(f"Updated weather record ID: {existing_record.id}")
            return existing_record
        else:
            # Create new weather record
            weather_record: models.WeatherRecord = models.WeatherRecord(
                location_id=location.id,
                condition_id=condition.id,
                localtime_epoch=localtime_epoch,
                localtime=localtime,
                **current_data,
            )

            db.add(weather_record)
            db.commit()
            db.refresh(weather_record)

            logger.success(f"Created weather record ID: {weather_record.id}")
            return weather_record

    except Exception as database_error:
        db.rollback()
        logger.error(f"Failed to create/update weather record: {database_error}")
        raise


def get_weather_record(db: Session, record_id: int) -> models.WeatherRecord | None:
    """
    Get a specific weather record by ID.

    Args:
        db: Database session
        record_id: ID of the weather record to retrieve

    Returns:
        WeatherRecord if found, None otherwise
    """
    return db.query(models.WeatherRecord).filter(models.WeatherRecord.id == record_id).first()


def get_weather_records(
    db: Session, skip: int = 0, limit: int = 100
) -> tuple[list[models.WeatherRecord], int]:
    """
    Get paginated weather records ordered by creation time (newest first).

    Args:
        db: Database session
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return

    Returns:
        Tuple of (records list, total count)
    """
    query = db.query(models.WeatherRecord).order_by(desc(models.WeatherRecord.created_at))
    total: int = query.count()
    records: list[models.WeatherRecord] = query.offset(skip).limit(limit).all()
    return records, total


def get_weather_by_location_exact(
    db: Session, location_name: str, skip: int = 0, limit: int = 100
) -> tuple[list[models.WeatherRecord], int]:
    """
    Get weather records for a specific location by exact name match.

    Args:
        db: Database session
        location_name: Exact location name to search for
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return

    Returns:
        Tuple of (records list, total count)
    """
    query: Any = (
        db.query(models.WeatherRecord)
        .join(models.Location)
        .filter(models.Location.name == location_name)
        .order_by(desc(models.WeatherRecord.created_at))
    )

    total: int = query.count()
    records: list[models.WeatherRecord] = query.offset(skip).limit(limit).all()
    return records, total


def get_weather_by_location(
    db: Session, location_name: str, skip: int = 0, limit: int = 100
) -> tuple[list[models.WeatherRecord], int]:
    """
    Get weather records for a location by partial name match (case-insensitive).

    Searches using ILIKE pattern matching to find locations whose name
    contains the search term. For exact matching, use get_weather_by_location_exact.

    Args:
        db: Database session
        location_name: Partial location name to search for
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return

    Returns:
        Tuple of (records list, total count)
    """
    query: Any = (
        db.query(models.WeatherRecord)
        .join(models.Location)
        .filter(models.Location.name.ilike(f"%{location_name}%"))
        .order_by(desc(models.WeatherRecord.created_at))
    )

    total: int = query.count()
    records: list[models.WeatherRecord] = query.offset(skip).limit(limit).all()
    return records, total


def get_latest_weather_by_location(db: Session, location_name: str) -> models.WeatherRecord | None:
    """
    Get the most recent weather record for a location.

    Searches using partial name match (case-insensitive).

    Args:
        db: Database session
        location_name: Partial location name to search for

    Returns:
        Most recent WeatherRecord if found, None otherwise
    """
    return (
        db.query(models.WeatherRecord)
        .join(models.Location)
        .filter(models.Location.name.ilike(f"%{location_name}%"))
        .order_by(desc(models.WeatherRecord.created_at))
        .first()
    )
