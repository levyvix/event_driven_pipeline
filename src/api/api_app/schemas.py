"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# Location schemas
class LocationBase(BaseModel):
    """Base schema for location data (without localtime)."""

    name: str
    """Location name"""

    region: str
    """Region/state name"""

    country: str
    """Country name"""

    lat: float
    """Latitude coordinate"""

    lon: float
    """Longitude coordinate"""

    tz_id: str
    """Timezone ID (e.g., America/New_York)"""


class LocationInput(LocationBase):
    """Location input schema (includes localtime for API input)"""

    localtime_epoch: int
    localtime: str


class LocationResponse(LocationBase):
    """Location response schema"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Weather condition schemas
class ConditionBase(BaseModel):
    """Base schema for weather condition"""

    text: str
    icon: str
    code: int


class ConditionResponse(ConditionBase):
    """Weather condition response schema"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Current weather schemas
class CurrentWeatherBase(BaseModel):
    """Base schema for current weather data"""

    last_updated_epoch: int
    last_updated: str
    temp_c: float
    temp_f: float
    is_day: int
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    feelslike_c: float
    feelslike_f: float
    windchill_c: float
    windchill_f: float
    heatindex_c: float
    heatindex_f: float
    dewpoint_c: float
    dewpoint_f: float
    vis_km: float
    vis_miles: float
    uv: float
    gust_mph: float
    gust_kph: float
    short_rad: float
    diff_rad: float
    dni: float
    gti: float


# Weather record request/response schemas
class WeatherRecordCreate(BaseModel):
    """Schema for creating a weather record (matches API input)"""

    location: LocationInput
    current: CurrentWeatherBase
    condition: ConditionBase = Field(..., alias="current.condition")

    model_config = {"populate_by_name": True}


class WeatherRecordResponse(BaseModel):
    """Schema for weather record response"""

    id: int
    location: LocationResponse
    condition: ConditionResponse

    # Timestamps
    localtime_epoch: int
    localtime: str
    last_updated_epoch: int
    last_updated: str

    # Temperature
    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float
    windchill_c: float
    windchill_f: float
    heatindex_c: float
    heatindex_f: float
    dewpoint_c: float
    dewpoint_f: float

    # Wind
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    gust_mph: float
    gust_kph: float

    # Atmospheric
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int

    # Visibility
    vis_km: float
    vis_miles: float

    # Solar
    uv: float
    short_rad: float
    diff_rad: float
    dni: float
    gti: float

    # Day/Night
    is_day: int

    # Record timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WeatherRecordList(BaseModel):
    """Schema for paginated weather records"""

    total: int
    page: int
    page_size: int
    records: list[WeatherRecordResponse]
