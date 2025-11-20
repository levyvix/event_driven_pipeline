"""End-to-End tests for the weather data pipeline"""

import asyncio
import json
import os
import time
from typing import Any

import httpx
import pika
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from api_app.config import settings
from api_app.models import WeatherRecord


# ========================
# Health Check Functions
# ========================


def check_rabbitmq_health(host: str, port: int) -> bool:
    """Check if RabbitMQ is healthy and reachable"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host, port, heartbeat=5, connection_attempts=1, blocked_connection_timeout=5
            )
        )
        connection.close()
        return True
    except Exception as e:
        raise ConnectionError(f"RabbitMQ unreachable at {host}:{port}: {e}")


def check_postgres_health(host: str, port: int, user: str, password: str, db: str) -> bool:
    """Check if PostgreSQL is healthy and reachable"""
    try:
        engine = create_engine(
            f"postgresql://{user}:{password}@{host}:{port}/{db}",
            pool_pre_ping=True,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception as e:
        raise ConnectionError(f"PostgreSQL unreachable at {host}:{port}: {e}")


async def check_metabase_health(url: str) -> bool:
    """Check if Metabase is healthy and reachable"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)
            # 200 is running, 302 is redirect to setup, 404 might be ok depending on state
            return response.status_code in [200, 302, 404]
    except Exception as e:
        raise ConnectionError(f"Metabase unreachable at {url}: {e}")


async def check_api_health(api_url: str) -> bool:
    """Check if API is healthy"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/health", timeout=5)
            return response.status_code == 200
    except Exception as e:
        raise ConnectionError(f"API unreachable at {api_url}: {e}")


# ========================
# Test Data Helpers
# ========================


def get_test_weather_message() -> dict:
    """Generate a valid test weather message matching OpenWeather API format"""
    return {
        "location": {
            "name": "Test City",
            "region": "Test Region",
            "country": "Test Country",
            "lat": 40.7128,
            "lon": -74.0060,
            "tz_id": "America/New_York",
            "localtime_epoch": 1700000000,
            "localtime": "2023-11-14 15:26:40",
        },
        "current": {
            "last_updated_epoch": 1700000000,
            "last_updated": "2023-11-14 15:26:40",
            "condition": {
                "code": 1000,
                "text": "Clear",
                "icon": "//cdn.weatherapi.com/weather/128x128/night/113.png",
            },
            "temp_c": 15.0,
            "temp_f": 59.0,
            "feelslike_c": 14.0,
            "feelslike_f": 57.2,
            "windchill_c": 13.5,
            "windchill_f": 56.3,
            "heatindex_c": 15.0,
            "heatindex_f": 59.0,
            "dewpoint_c": 5.0,
            "dewpoint_f": 41.0,
            "wind_mph": 10.5,
            "wind_kph": 16.9,
            "wind_degree": 180,
            "wind_dir": "S",
            "gust_mph": 15.0,
            "gust_kph": 24.1,
            "pressure_mb": 1013.0,
            "pressure_in": 29.91,
            "precip_mm": 0.0,
            "precip_in": 0.0,
            "humidity": 65,
            "cloud": 10,
            "vis_km": 10.0,
            "vis_miles": 6.2,
            "uv": 0.0,
            "short_rad": 0.0,
            "diff_rad": 0.0,
            "dni": 0.0,
            "gti": 0.0,
            "is_day": 0,
        },
    }


# ========================
# E2E Pipeline Tests
# ========================


@pytest.mark.asyncio
async def test_service_health_checks(
    api_url: str, rabbitmq_config: dict, postgres_config: dict, metabase_url: str
):
    """Test that all services are healthy and reachable"""
    # Check RabbitMQ
    assert check_rabbitmq_health(rabbitmq_config["host"], rabbitmq_config["port"])

    # Check PostgreSQL
    assert check_postgres_health(
        postgres_config["host"],
        postgres_config["port"],
        postgres_config["user"],
        postgres_config["password"],
        postgres_config["db"],
    )

    # Check API
    assert await check_api_health(api_url)

    # Check Metabase (optional - may not be running)
    try:
        assert await check_metabase_health(metabase_url)
    except ConnectionError:
        pytest.skip("Metabase not running (optional service)")


@pytest.mark.asyncio
async def test_full_pipeline(
    test_client, test_db_session: Session, rabbitmq_config: dict, postgres_config: dict
):
    """Test the complete pipeline: RabbitMQ -> Consumer -> API -> Database"""

    # Generate test message
    test_message = get_test_weather_message()

    # Publish message to RabbitMQ
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                rabbitmq_config["host"],
                rabbitmq_config["port"],
                heartbeat=5,
                connection_attempts=3,
            )
        )
        channel = connection.channel()
        # Declare queue passively (don't modify existing queue properties)
        try:
            channel.queue_declare(queue=rabbitmq_config["queue_name"], passive=True)
        except pika.exceptions.ChannelClosedByBroker:
            # Queue doesn't exist, create it
            channel = connection.channel()
            channel.queue_declare(queue=rabbitmq_config["queue_name"])

        channel.basic_publish(
            exchange="",
            routing_key=rabbitmq_config["queue_name"],
            body=json.dumps(test_message),
        )
        connection.close()
    except Exception as e:
        pytest.fail(f"Failed to publish message to RabbitMQ: {e}")

    # Poll the database for the record to appear (allow consumer time to process)
    max_attempts = 60  # 60 seconds total
    poll_interval = 1  # 1 second between polls
    record = None

    for attempt in range(max_attempts):
        # Query the database for a record matching our test data
        record = (
            test_db_session.query(WeatherRecord)
            .filter(WeatherRecord.localtime_epoch == test_message["location"]["localtime_epoch"])
            .first()
        )

        if record:
            break

        await asyncio.sleep(poll_interval)

    # Verify record was created
    assert record is not None, "Consumer did not process message in time (30+ seconds)"

    # Verify record fields match input data
    assert record.temp_c == test_message["current"]["temp_c"]
    assert record.humidity == test_message["current"]["humidity"]
    assert record.wind_kph == test_message["current"]["wind_kph"]

    # Verify location data
    assert record.location.name == test_message["location"]["name"]
    assert record.location.lat == test_message["location"]["lat"]
    assert record.location.lon == test_message["location"]["lon"]

    # Verify condition data
    assert record.condition.code == test_message["current"]["condition"]["code"]
    assert record.condition.text == test_message["current"]["condition"]["text"]

    # Verify timestamps
    assert record.created_at is not None
    assert record.updated_at is not None
    assert record.created_at <= record.updated_at


@pytest.mark.asyncio
async def test_upsert_idempotency(test_client, test_db_session: Session, rabbitmq_config: dict):
    """Test that duplicate messages don't create duplicate records (upsert pattern)"""

    test_message = get_test_weather_message()

    # Function to publish message
    def publish_message():
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    rabbitmq_config["host"],
                    rabbitmq_config["port"],
                    heartbeat=5,
                    connection_attempts=3,
                )
            )
            channel = connection.channel()
            # Declare queue passively (don't modify existing queue properties)
            try:
                channel.queue_declare(queue=rabbitmq_config["queue_name"], passive=True)
            except pika.exceptions.ChannelClosedByBroker:
                # Queue doesn't exist, create it
                channel = connection.channel()
                channel.queue_declare(queue=rabbitmq_config["queue_name"])

            channel.basic_publish(
                exchange="",
                routing_key=rabbitmq_config["queue_name"],
                body=json.dumps(test_message),
            )
            connection.close()
        except Exception as e:
            pytest.fail(f"Failed to publish message: {e}")

    # Publish message first time
    publish_message()

    # Wait for message to be processed
    record_1_id = None
    for attempt in range(60):
        record = (
            test_db_session.query(WeatherRecord)
            .filter(WeatherRecord.localtime_epoch == test_message["location"]["localtime_epoch"])
            .first()
        )
        if record:
            record_1_id = record.id
            created_at_1 = record.created_at
            updated_at_1 = record.updated_at
            break
        await asyncio.sleep(1)

    assert record_1_id is not None, "First message not processed"

    # Wait a bit before publishing duplicate
    await asyncio.sleep(2)

    # Publish same message again
    publish_message()

    # Wait for second message to be processed
    for attempt in range(60):
        test_db_session.expire_all()  # Refresh from DB
        record = (
            test_db_session.query(WeatherRecord)
            .filter(WeatherRecord.localtime_epoch == test_message["location"]["localtime_epoch"])
            .first()
        )
        if record and record.updated_at > updated_at_1:
            # Record was updated
            break
        await asyncio.sleep(1)

    # Verify only one record exists (not two)
    count = (
        test_db_session.query(WeatherRecord)
        .filter(WeatherRecord.localtime_epoch == test_message["location"]["localtime_epoch"])
        .count()
    )
    assert count == 1, f"Expected 1 record, but found {count} (upsert failed)"

    # Verify created_at didn't change
    updated_record = (
        test_db_session.query(WeatherRecord)
        .filter(WeatherRecord.id == record_1_id)
        .first()
    )
    assert updated_record.created_at == created_at_1, "created_at should not change on upsert"
    assert updated_record.updated_at >= updated_at_1, "updated_at should be updated on upsert"


@pytest.mark.asyncio
async def test_api_accepts_weather_data(test_client):
    """Test that the API accepts weather data and returns 201 Created"""

    test_message = get_test_weather_message()

    # POST to API directly
    response = test_client.post("/api/weather", json=test_message)

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    # Verify response contains record ID
    data = response.json()
    assert "id" in data
    assert data["temp_c"] == test_message["current"]["temp_c"]


@pytest.mark.asyncio
async def test_api_weather_record_retrieval(test_client, test_db_session: Session):
    """Test that weather records can be retrieved via API"""

    # Create a test record via API
    test_message = get_test_weather_message()
    response = test_client.post("/api/weather", json=test_message)
    assert response.status_code == 201

    record_id = response.json()["id"]

    # Retrieve the record
    get_response = test_client.get(f"/api/weather/{record_id}")
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["id"] == record_id
    assert data["temp_c"] == test_message["current"]["temp_c"]
