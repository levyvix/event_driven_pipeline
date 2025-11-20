"""SQLAlchemy ORM models for weather data storage."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Location(Base):
    """Location information for weather data"""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    region = Column(String(255), nullable=False)
    country = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    tz_id = Column(String(100), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    weather_records = relationship("WeatherRecord", back_populates="location")

    # Composite index for location lookups
    __table_args__ = (
        Index("idx_location_coords", "lat", "lon"),
        Index("idx_location_name_country", "name", "country"),
    )


class WeatherCondition(Base):
    """Weather condition types (e.g., Partly cloudy, Sunny, etc.)"""

    __tablename__ = "weather_conditions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Integer, unique=True, nullable=False, index=True)
    text = Column(String(255), nullable=False)
    icon = Column(String(255), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    weather_records = relationship("WeatherRecord", back_populates="condition")


class WeatherRecord(Base):
    """Current weather measurements"""

    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    condition_id = Column(Integer, ForeignKey("weather_conditions.id"), nullable=False)

    # Timestamp from API
    localtime_epoch = Column(Integer, nullable=False)
    localtime = Column(String(50), nullable=False)
    last_updated_epoch = Column(Integer, nullable=False)
    last_updated = Column(String(50), nullable=False)

    # Temperature
    temp_c = Column(Float, nullable=False)
    temp_f = Column(Float, nullable=False)
    feelslike_c = Column(Float, nullable=False)
    feelslike_f = Column(Float, nullable=False)
    windchill_c = Column(Float, nullable=False)
    windchill_f = Column(Float, nullable=False)
    heatindex_c = Column(Float, nullable=False)
    heatindex_f = Column(Float, nullable=False)
    dewpoint_c = Column(Float, nullable=False)
    dewpoint_f = Column(Float, nullable=False)

    # Wind
    wind_mph = Column(Float, nullable=False)
    wind_kph = Column(Float, nullable=False)
    wind_degree = Column(Integer, nullable=False)
    wind_dir = Column(String(10), nullable=False)
    gust_mph = Column(Float, nullable=False)
    gust_kph = Column(Float, nullable=False)

    # Atmospheric
    pressure_mb = Column(Float, nullable=False)
    pressure_in = Column(Float, nullable=False)
    precip_mm = Column(Float, nullable=False)
    precip_in = Column(Float, nullable=False)
    humidity = Column(Integer, nullable=False)
    cloud = Column(Integer, nullable=False)

    # Visibility
    vis_km = Column(Float, nullable=False)
    vis_miles = Column(Float, nullable=False)

    # Solar radiation
    uv = Column(Float, nullable=False)
    short_rad = Column(Float, nullable=False)
    diff_rad = Column(Float, nullable=False)
    dni = Column(Float, nullable=False)
    gti = Column(Float, nullable=False)

    # Day/Night
    is_day = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="weather_records")
    condition = relationship("WeatherCondition", back_populates="weather_records")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_weather_location_created", "location_id", "created_at"),
        Index("idx_weather_last_updated", "last_updated_epoch"),
        Index("idx_weather_upsert", "location_id", "condition_id", "localtime_epoch"),
    )
