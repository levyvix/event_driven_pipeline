# Design: End-to-End Testing Architecture

## Overview

This document outlines the technical approach for automated end-to-end testing of the event-driven weather pipeline. The goal is to validate that a fresh clone can run successfully with all services operational.

## Architecture

```
Test Runner (Python/pytest)
  ↓
  1. Verify All Services Healthy
     ├─ API /health → 200 OK
     ├─ RabbitMQ → pika connection success
     ├─ PostgreSQL → psycopg3 connection success
     └─ Metabase → HTTP 200 on port 3000
  ↓
  2. Publish Test Message
     └─ Send sample weather JSON to RabbitMQ queue "weather"
  ↓
  3. Wait for Processing
     └─ Poll database for new weather_records (max 30 seconds)
  ↓
  4. Verify Pipeline Output
     ├─ Confirm record exists in database
     ├─ Verify consumer processed message (check logs)
     └─ API should have returned 201 Created
```

## Component Details

### 1. Health Checks

**API Health Endpoint** (`GET /health`)
- Already exists in `src/api/api_app/main.py`
- Returns: `{"status": "ok"}`
- Validates FastAPI is running and DB connection works

**RabbitMQ Health Check**
- Establish pika connection to `RABBIT_HOST:5672`
- Send test message to verify queue exists
- Connection should succeed without timeouts

**PostgreSQL Health Check**
- Attempt `SELECT 1` via psycopg
- Verify `weather_records` table exists (via `\dt` or SELECT count(*) FROM information_schema.tables)

**Metabase Health Check**
- HTTP GET to `http://metabase:3000` (or localhost:3000 in local mode)
- Expect HTTP 200
- Optionally verify PostgreSQL connection in Metabase settings (requires login, so basic HTTP check is sufficient)

### 2. E2E Test Flow

**Setup Phase**
- Require all containers running (docker compose ps)
- Clear any test data from previous runs (DELETE FROM weather_records WHERE ... OR use test isolation)
- Note the current time as baseline for polling

**Test Publish**
- Send a sample weather JSON to RabbitMQ queue "weather"
- Message format matches producer output:
  ```json
  {
    "location": {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco", "country": "US"},
    "current": {
      "temp": 25.0,
      "feels_like": 24.5,
      "humidity": 65,
      "wind_speed": 5.2,
      "weather": [{"id": 800, "main": "Clear"}],
      "dt": 1700000000
    }
  }
  ```

**Poll for Result**
- Query: `SELECT COUNT(*) FROM weather_records WHERE created_at > :baseline_time`
- Retry every 1 second for up to 30 seconds
- Expected: 1 new record created
- If timeout: Fail test with message "Consumer did not process message within 30s"

**Verify Record Integrity**
- Check fields match input: location coordinates, weather temp, humidity, etc.
- Verify timestamps: `created_at` should be within last 30 seconds, `updated_at` ≥ `created_at`

**Verify Upsert** (optional, advanced)
- Send same weather JSON again
- Verify record count remains 1 (upsert, not insert)
- Verify `updated_at` changed but `created_at` did not

### 3. Test Execution

**Via pytest**
```bash
cd src/api
uv run pytest tests/test_e2e_pipeline.py -v
```

**Via standalone script** (backup, for initial setup validation)
```bash
cd docker
python ../scripts/e2e_test.py
```

**Environment**
- Requires `OPENWEATHER_API_KEY` in `.env` (even for E2E, as producer may fetch)
- Uses docker-compose network: connect to `postgres:5432`, `rabbit-mq:5672`, `metabase:3000`
- For local development: connect to `localhost:8000`, `localhost:5672`, etc.

## Error Scenarios & Messages

| Scenario | Check | Error Message | Recovery |
|----------|-------|---------------|----------|
| API not running | GET /health timeout | "API failed to respond within 5s" | `docker compose logs api` |
| RabbitMQ not running | pika connect fail | "RabbitMQ unreachable at rabbit-mq:5672" | `docker compose logs rabbit-mq` |
| PostgreSQL not healthy | SELECT 1 fails | "PostgreSQL failed to respond" | Check `docker compose ps` for health status |
| Consumer not processing | No new records after 30s | "Consumer did not process message in time" | `docker compose logs consumer` |
| Metabase unreachable | HTTP GET port 3000 timeout | "Metabase failed to respond" | `docker compose logs metabase` |
| Data mismatch | Record fields don't match | "Weather record fields don't match input" | Inspect database directly |

## Implementation Plan

### File Structure
```
src/api/
├── tests/
│   ├── __init__.py
│   ├── conftest.py (pytest fixtures: db_session, test_client)
│   ├── test_e2e_pipeline.py (main E2E test)
│   └── test_health_checks.py (service health tests)
└── pyproject.toml (ensure pytest, httpx, pika, psycopg in dev deps)

scripts/
└── e2e_test.py (standalone Python script for pre-container setup validation)

docker/
└── (existing docker-compose.yaml, no changes needed)

CLAUDE.md
└── (add E2E Testing section)
```

### Dependencies
- **pytest**: Already in `api/pyproject.toml`
- **httpx**: For HTTP health checks (async HTTP client, already in dev deps)
- **pika**: For RabbitMQ health check (producer already uses it)
- **psycopg3**: For PostgreSQL connection check (api already uses sqlalchemy, which depends on it)
- No new dependencies required

### Phased Rollout
1. **Phase 1**: Health checks + basic E2E test (docker environment)
2. **Phase 2**: Pytest fixtures for cleaner test code + upsert validation
3. **Phase 3**: Documentation + troubleshooting guide + CI/CD integration

## Testing the Test

- Manually run full pipeline: `docker compose up -d && sleep 10 && pytest tests/test_e2e_pipeline.py`
- Verify it passes with fresh containers
- Simulate failure: Stop consumer and re-run test, expect timeout
- Simulate failure: Clear API dependency and re-run, expect API health check failure

## Open Questions

1. Should E2E test run automatically on container startup, or only on-demand?
   - **Decision**: On-demand (run via pytest or script after setup verification)
2. Should we test multiple locations, or just one?
   - **Decision**: One location (same as producer's current implementation)
3. How long to wait for consumer to process before timeout?
   - **Decision**: 30 seconds (accounts for container startup delays)
