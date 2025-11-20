#!/usr/bin/env python3
"""
Standalone E2E test script for weather data pipeline
Run without pytest from any environment to verify the full pipeline works
"""

import asyncio
import json
import os
import sys
import time

try:
    import httpx
    import pika
    from sqlalchemy import create_engine, text
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Install with: pip install httpx pika sqlalchemy psycopg")
    sys.exit(1)

# ========================
# Configuration
# ========================

API_URL = os.getenv("API_URL", "http://localhost:8000")
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
QUEUE_NAME = os.getenv("QUEUE_NAME", "weather")
METABASE_URL = os.getenv("METABASE_URL", "http://localhost:3000")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "weather_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "weather_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "weather_db")

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


# ========================
# Utility Functions
# ========================


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{text}{RESET}")
    print("-" * len(text))


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"  {text}")


# ========================
# Health Check Functions
# ========================


def check_rabbitmq_health() -> bool:
    """Check if RabbitMQ is healthy"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(RABBIT_HOST, RABBIT_PORT, heartbeat=5, connection_attempts=1)
        )
        connection.close()
        print_success(f"RabbitMQ healthy ({RABBIT_HOST}:{RABBIT_PORT})")
        return True
    except Exception as e:
        print_error(f"RabbitMQ unreachable: {e}")
        return False


async def check_api_health() -> bool:
    """Check if API is healthy"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                print_success(f"API healthy ({API_URL})")
                return True
            else:
                print_error(f"API returned status {response.status_code}")
                return False
    except Exception as e:
        print_error(f"API unreachable: {e}")
        return False


def check_postgres_health() -> bool:
    """Check if PostgreSQL is healthy"""
    try:
        engine = create_engine(
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
            pool_pre_ping=True,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        print_success(f"PostgreSQL healthy ({POSTGRES_HOST}:{POSTGRES_PORT})")
        return True
    except Exception as e:
        print_error(f"PostgreSQL unreachable: {e}")
        return False


async def check_metabase_health() -> bool:
    """Check if Metabase is healthy (optional)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(METABASE_URL, timeout=5)
            if response.status_code in [200, 302, 404]:
                print_success(f"Metabase healthy ({METABASE_URL})")
                return True
            else:
                print_warning(f"Metabase returned status {response.status_code}")
                return False
    except Exception as e:
        print_warning(f"Metabase not running (optional): {e}")
        return False


# ========================
# Test Data
# ========================


def get_test_weather_message() -> dict:
    """Generate test weather message"""
    now = int(time.time())
    return {
        "location": {
            "name": "E2E Test City",
            "region": "Test Region",
            "country": "Test Country",
            "lat": 40.7128,
            "lon": -74.0060,
            "tz_id": "America/New_York",
            "localtime_epoch": now,
            "localtime": "2023-11-14 15:26:40",
        },
        "current": {
            "last_updated_epoch": now,
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
# Pipeline Test
# ========================


async def test_pipeline() -> bool:
    """Test the full pipeline"""
    test_message = get_test_weather_message()
    localtime_epoch = test_message["location"]["localtime_epoch"]

    print_header("Publishing Test Message to RabbitMQ")
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(RABBIT_HOST, RABBIT_PORT, heartbeat=5, connection_attempts=3)
        )
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)
        channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(test_message))
        connection.close()
        print_success(f"Message published to queue '{QUEUE_NAME}'")
    except Exception as e:
        print_error(f"Failed to publish message: {e}")
        return False

    print_header("Waiting for Message Processing")
    print_info("Waiting for consumer to process message and API to create record...")
    print_info("(checking database every 1 second for up to 60 seconds)")

    # Poll database for record
    engine = create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        pool_pre_ping=True,
    )

    for attempt in range(60):
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT id, temp_c, humidity FROM weather_records "
                        "WHERE localtime_epoch = :epoch"
                    ),
                    {"epoch": localtime_epoch},
                )
                row = result.fetchone()
                if row:
                    record_id, temp_c, humidity = row
                    print_success(f"Record created in database (ID: {record_id})")
                    print_info(f"  Temperature: {temp_c}°C")
                    print_info(f"  Humidity: {humidity}%")
                    engine.dispose()
                    return True
        except Exception as e:
            print_error(f"Database query failed: {e}")
            engine.dispose()
            return False

        await asyncio.sleep(1)
        print_info(f"Attempt {attempt + 1}/60 - waiting...")

    print_error("Record not created in database after 60 seconds")
    engine.dispose()
    return False


# ========================
# Main
# ========================


async def main():
    """Run all checks"""
    print(f"\n{BOLD}Weather Pipeline E2E Test{RESET}")
    print("Testing pipeline: RabbitMQ → Consumer → API → PostgreSQL")
    print(f"\n{BOLD}Configuration:{RESET}")
    print_info(f"API URL: {API_URL}")
    print_info(f"RabbitMQ: {RABBIT_HOST}:{RABBIT_PORT} (queue: {QUEUE_NAME})")
    print_info(f"PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print_info(f"Metabase: {METABASE_URL}")

    print_header("Phase 1: Service Health Checks")

    all_healthy = True

    if not check_rabbitmq_health():
        all_healthy = False

    if not await check_api_health():
        all_healthy = False

    if not check_postgres_health():
        all_healthy = False

    await check_metabase_health()  # Optional - don't fail if missing

    if not all_healthy:
        print_error("\nCritical services not healthy. Aborting pipeline test.")
        return False

    print_success("All critical services healthy!")

    print_header("Phase 2: Full Pipeline Test")

    pipeline_ok = await test_pipeline()

    print_header("Summary")
    if pipeline_ok:
        print_success("E2E test PASSED! Pipeline is working correctly.")
        return True
    else:
        print_error("E2E test FAILED! See errors above for details.")
        print_warning("\nTroubleshooting tips:")
        print_info("1. Verify all services are running: docker compose ps")
        print_info("2. Check consumer logs: docker compose logs consumer")
        print_info("3. Check API logs: docker compose logs api")
        print_info(
            "4. Verify RabbitMQ queue: docker exec docker-rabbit-mq-1 rabbitmq-admin list queues"
        )
        print_info(
            "5. Check database records: docker exec docker-postgres-1 psql "
            "-U $POSTGRES_USER -d $POSTGRES_DB -c 'SELECT COUNT(*) FROM "
            "weather_records'"
        )
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        sys.exit(1)
