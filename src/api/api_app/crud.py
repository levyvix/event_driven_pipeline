from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session

from api_app import models


def get_or_create_location(db: Session, location_data: dict) -> models.Location:
    """Get existing location or create new one"""
    location = (
        db.query(models.Location)
        .filter(
            models.Location.name == location_data["name"],
            models.Location.country == location_data["country"],
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


def get_or_create_condition(db: Session, condition_data: dict) -> models.WeatherCondition:
    """Get existing weather condition or create new one"""
    condition = (
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


def create_weather_record(db: Session, weather_data: dict) -> models.WeatherRecord:
    """Create or update a weather record (upsert pattern)"""
    try:
        # Extract nested data
        location_data_raw = weather_data["location"].copy()
        current_data = weather_data["current"].copy()
        condition_data = current_data.pop("condition")

        # Extract localtime fields from location data (they belong to weather record)
        localtime_epoch = location_data_raw.pop("localtime_epoch")
        localtime = location_data_raw.pop("localtime")

        # Get or create related entities
        location = get_or_create_location(db, location_data_raw)
        condition = get_or_create_condition(db, condition_data)

        # Check if record already exists (same location, condition, and timestamp)
        existing_record = (
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
            weather_record = models.WeatherRecord(
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

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create/update weather record: {e}")
        raise


def get_weather_record(db: Session, record_id: int) -> models.WeatherRecord | None:
    """Get a specific weather record by ID"""
    return db.query(models.WeatherRecord).filter(models.WeatherRecord.id == record_id).first()


def get_weather_records(
    db: Session, skip: int = 0, limit: int = 100
) -> tuple[list[models.WeatherRecord], int]:
    """Get paginated weather records"""
    query = db.query(models.WeatherRecord).order_by(desc(models.WeatherRecord.created_at))
    total = query.count()
    records = query.offset(skip).limit(limit).all()
    return records, total


def get_weather_by_location(
    db: Session, location_name: str, skip: int = 0, limit: int = 100
) -> tuple[list[models.WeatherRecord], int]:
    """Get weather records for a specific location"""
    query = (
        db.query(models.WeatherRecord)
        .join(models.Location)
        .filter(models.Location.name.ilike(f"%{location_name}%"))
        .order_by(desc(models.WeatherRecord.created_at))
    )

    total = query.count()
    records = query.offset(skip).limit(limit).all()
    return records, total


def get_latest_weather_by_location(db: Session, location_name: str) -> models.WeatherRecord | None:
    """Get the most recent weather record for a location"""
    return (
        db.query(models.WeatherRecord)
        .join(models.Location)
        .filter(models.Location.name.ilike(f"%{location_name}%"))
        .order_by(desc(models.WeatherRecord.created_at))
        .first()
    )
