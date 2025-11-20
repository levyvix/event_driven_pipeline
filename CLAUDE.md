<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

```bash
# Start all services (from docker/ directory)
docker compose up -d

# Start only database for local development
docker compose up postgres rabbit-mq -d

# Run a single service locally
cd src/api && uv run uvicorn api_app.main:app --reload
cd src/producer && uv run python -m producer_app.api_fetcher
cd src/consumer && uv run python -m consumer_app.message_consumer

# Generate database migration (after modifying models)
cd src/api && uv run alembic revision --autogenerate -m "description"

# Apply database migrations
cd src/api && uv run alembic upgrade head

# Check logs
docker compose logs -f [service-name]

# Stop all services
docker compose down

# Stop and remove volumes (clears database)
docker compose down -v

# Query database directly
docker exec docker-postgres-1 psql -U weather_user -d weather_db -c "\dt"

# Access Metabase dashboard (if running)
# Navigate to http://localhost:3000 in your browser
```

## Pre-commit Setup

Pre-commit hooks ensure code quality by running linters and formatters automatically on commit.

### First-time setup

```bash
cd src/api
uv sync --group dev  # Install dev dependencies (includes pre-commit)
uv run pre-commit install  # Install git hooks
```

### Running pre-commit

```bash
# Run on all files
cd src/api && uv run pre-commit run --all-files

# Run automatically on git commit
git add .
git commit -m "your message"  # hooks run automatically

# Update hook versions to latest
cd src/api && uv run pre-commit autoupdate
```

### What pre-commit checks

- **Standard hooks**: Trailing whitespace, end-of-file fixing, YAML/JSON/TOML validation
- **Ruff linting**: Code quality checks on API and scripts (unused imports, style issues)
- **Ruff formatting**: Automatic code formatting on all Python files
- **Security**: Detects private keys, merge conflicts, large files (>1MB)

## Metabase Dashboard (Optional)

Metabase is a lightweight BI tool for visualizing weather data without writing SQL. It's optional—all data remains accessible via API queries.

### Quick Start

1. **Start Metabase** (requires PostgreSQL running):
   ```bash
   docker compose up -d metabase
   ```
   - Metabase starts at `http://localhost:3000`
   - First startup: You'll see a welcome wizard (takes ~30 seconds)

2. **Create Admin User** (first login only):
   - Go to `http://localhost:3000`
   - Fill in: email, password, company name, preferred language
   - Click "Take me to Metabase"

3. **Metabase Auto-Detects Database**:
   - PostgreSQL connection is automatically configured (via env vars in docker-compose.yaml)
   - You'll see "Browse Data" with three tables: `locations`, `weather_conditions`, `weather_records`
   - Click each table to explore schema and sample data

### Creating Dashboards (Manual via UI)

Metabase dashboards are created through the web UI—no code required. Example workflows:

#### Dashboard 1: Weather Timeline
- **Purpose**: Track weather observations over time
- **Step 1**: Click "New" → "Question"
- **Step 2**: Select table: `weather_records`
- **Step 3**: Aggregate: "Count of records" grouped by "created_at" (aggregation: hourly)
- **Step 4**: Visualize as "Line Chart" or "Area Chart"
- **Step 5**: Add filter: Location (dropdown)
- **Step 6**: Save as dashboard card titled "Weather Timeline"

#### Dashboard 2: Weather Trends
- **Purpose**: Average temperature and humidity by location
- **Step 1**: Create new question from `weather_records`
- **Step 2**: Aggregate: "Average of temperature" grouped by location → "Average of humidity" grouped by location
- **Step 3**: Visualize as "Bar Chart" or "Line Chart"
- **Step 4**: Add optional date range filter
- **Step 5**: Save to dashboard

#### Dashboard 3: Data Freshness Monitoring
- **Purpose**: Monitor pipeline health (record counts, latest updates)
- **Step 1**: Create new question (KPI cards)
   - Card 1: Count of records: `SELECT COUNT(*) FROM weather_records`
   - Card 2: Records from last hour: `SELECT COUNT(*) FROM weather_records WHERE created_at > NOW() - INTERVAL '1 hour'`
   - Card 3: Latest update: `SELECT MAX(updated_at) FROM weather_records`
- **Step 2**: Save to "Data Freshness" dashboard

### Stopping Metabase

```bash
docker compose down metabase  # Stop without losing data
docker compose down -v        # Stop and remove all volumes (clears Metabase state)
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Metabase won't start | Check PostgreSQL is healthy: `docker compose ps` (look for `healthy` status) |
| Can't connect to database | Verify POSTGRES_* env vars match docker-compose.yaml environment section |
| Slow queries | Metabase caches results for 1 hour (configurable in settings); refresh manually if needed |
| Admin password forgotten | No recovery; recreate with `docker compose down -v && docker compose up -d metabase` |

## Architecture Overview

**Event-Driven Weather Pipeline**: A 5-layer system that fetches weather data, processes it asynchronously, and persists it.

```
Producer → RabbitMQ → Consumer → FastAPI → PostgreSQL
  ↑                                           ↓
  └─────── Scheduled hourly ────────────────┘
```

### Data Flow
1. **Producer** (Python + requests): Fetches weather from OpenWeather API every hour, publishes raw JSON to RabbitMQ queue "weather"
2. **RabbitMQ**: Message broker with manual ACK/NACK handling (prefetch_count=1)
3. **Consumer** (Python + pika): Listens continuously, HTTP POSTs each message to internal API, retries on network errors, rejects malformed JSON
4. **API** (FastAPI + SQLAlchemy): 6 endpoints, creates/links location and weather condition records, persists to DB
5. **PostgreSQL**: 3 tables (locations, weather_conditions, weather_records) with composite indexes for common queries

## Project Structure

```
src/
├── producer/          # Hourly weather data fetcher
│   ├── api_fetcher.py       # Main logic (fetches, publishes to queue)
│   └── config.py            # Settings via Pydantic (env vars)
├── consumer/          # Async message processor
│   ├── message_consumer.py  # Main logic (queue listener, HTTP client)
│   └── config.py            # Settings via Pydantic
└── api/              # Data persistence layer
    ├── main.py              # 6 FastAPI endpoints (POST/GET)
    ├── models.py            # 3 SQLAlchemy ORM models
    ├── database.py          # Connection pooling, session factory
    ├── crud.py              # get_or_create_location/condition, create_weather_record
    ├── schemas.py           # Pydantic request/response models
    ├── config.py            # Settings, database URL construction
    └── alembic/             # Database migrations (SQLAlchemy declarative)
```

## Configuration & Environment

Each service loads settings from `.env` (project root) using Pydantic BaseSettings.

**Producer needs**:
- `OPENWEATHER_API_KEY` (required)
- `RABBIT_HOST` (default: localhost)
- `QUEUE_NAME` (default: "weather")

**Consumer needs**:
- `RABBIT_HOST` (default: localhost)
- `QUEUE_NAME` (default: "weather")
- `API_URL` (default: http://localhost:8000/api/weather)

**API needs**:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

In Docker, environment variables are passed via `docker-compose.yaml` and `.env` file (producer/consumer only).

## Common Development Tasks

### Adding a new API endpoint
1. Define Pydantic schema in `src/api/api_app/schemas.py`
2. Add SQLAlchemy query in `src/api/api_app/crud.py`
3. Add route in `src/api/api_app/main.py` (use `Depends(get_db)` for session)

### Modifying database schema
1. Edit SQLAlchemy model in `src/api/api_app/models.py`
2. Generate migration: `cd src/api && uv run alembic revision --autogenerate -m "your description"`
3. Review generated file in `src/api/alembic/versions/`
4. Apply: `uv run alembic upgrade head`
5. Migration runs automatically on API container startup via entrypoint script

### E2E Testing

Automated E2E tests verify the entire pipeline from RabbitMQ → Consumer → API → Database.

#### Quick Start (with pytest)

```bash
# Start all services
docker compose up -d

# Wait for services to be healthy
sleep 15

# Run E2E tests
cd src/api
uv sync --group dev
uv run pytest tests/test_e2e_pipeline.py -v
```

**Expected output**: All tests pass with status like `test_service_health_checks PASSED`, `test_full_pipeline PASSED`, etc.

#### Standalone Test Script (no pytest required)

```bash
# Start all services
docker compose up -d

# Run standalone test from project root
python scripts/e2e_test.py
```

This script:
- Checks all services are healthy (RabbitMQ, PostgreSQL, API, Metabase)
- Publishes a test weather message to RabbitMQ
- Waits up to 60 seconds for the message to flow through Consumer → API → Database
- Verifies the record was created with correct fields

**Expected output**:
```
Weather Pipeline E2E Test
Testing pipeline: RabbitMQ → Consumer → API → PostgreSQL

Configuration:
  API URL: http://localhost:8000
  RabbitMQ: localhost:5672 (queue: weather)
  PostgreSQL: localhost:5432/weather_db
  Metabase: http://localhost:3000

Phase 1: Service Health Checks
✓ RabbitMQ healthy (localhost:5672)
✓ API healthy (http://localhost:8000)
✓ PostgreSQL healthy (localhost:5432)
✓ Metabase healthy (http://localhost:3000)
All critical services healthy!

Phase 2: Full Pipeline Test
...
✓ E2E test PASSED! Pipeline is working correctly.
```

### Testing the full pipeline locally

Run automated E2E tests (recommended) or manual steps:

**Automated (recommended):**
```bash
cd src/api && uv run pytest tests/test_e2e_pipeline.py -v
```

**Manual verification:**
1. Start services: `docker compose up -d`
2. Verify API is up: `curl http://localhost:8000/health`
3. Check database has tables: `docker exec docker-postgres-1 psql -U weather_user -d weather_db -c "\dt"`
4. Wait for producer to run (next :00 minute), check RabbitMQ queue: `docker exec docker-rabbit-mq-1 rabbitmq-admin list queues` (requires management plugin)
5. Check database for new records: `docker exec docker-postgres-1 psql -U weather_user -d weather_db -c "SELECT COUNT(*) FROM weather_records;"`

### Testing the upsert pattern
To verify that duplicate weather observations don't create multiple records:
1. POST same weather data to API twice:
   ```bash
   curl -X POST http://localhost:8000/api/weather -H "Content-Type: application/json" -d '{"location": {...}, "current": {...}}'
   ```
2. Verify both POSTs return the **same record ID** (not incrementing)
3. Verify `SELECT COUNT(*) FROM weather_records` shows **1 record** (not 2)
4. Verify `updated_at` timestamp is newer on second POST but `created_at` is unchanged

### Debugging a service
```bash
# View logs for specific service
docker compose logs -f producer    # or consumer, api, postgres
docker compose logs producer --tail 50  # Last 50 lines

# Connect to running container
docker exec -it docker-api-1 /bin/bash

# Test API endpoint
curl -X GET http://localhost:8000/api/weather?page=1&page_size=10
curl -X GET http://localhost:8000/health
```

### E2E Test Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Consumer did not process message in time"** | Check consumer is running: `docker compose logs consumer`. Verify RABBIT_HOST and QUEUE_NAME env vars. Consumer may be slow to start; wait 10-15 seconds after `docker compose up`. |
| **"RabbitMQ unreachable"** | Verify RabbitMQ is running: `docker compose ps rabbit-mq`. Check port 5672 is accessible. If using docker-compose, use `rabbit-mq` as hostname not `localhost`. |
| **"PostgreSQL unreachable"** | Verify PostgreSQL is running and healthy: `docker compose ps postgres`. Check password and user in `.env`. Run migrations: `docker exec docker-api-1 uv run alembic upgrade head`. |
| **"API health check failed"** | Verify API container is running: `docker compose logs api`. Check migrations ran. Verify POSTGRES_* env vars match database. |
| **Database connection refused** | Ensure PostgreSQL is healthy: `docker compose exec postgres pg_isready`. If unhealthy, reinitialize: `docker compose down -v && docker compose up -d postgres && sleep 10`. |
| **Test hangs waiting for message** | Consumer not connected. Check consumer logs: `docker compose logs consumer`. Verify it says "Listening for messages on queue 'weather'". |
| **API returns 500 on weather POST** | Check API logs: `docker compose logs api`. May be database schema issue. Run: `docker compose exec api uv run alembic upgrade head` and retry. |
| **pytest collection fails** | Install dev dependencies: `cd src/api && uv sync --group dev`. Verify Python 3.11+: `python --version`. |

**Quick reset if stuck:**
```bash
# Stop and remove all volumes (clears database state)
docker compose down -v

# Start fresh with a short wait
docker compose up -d
sleep 20

# Try test again
python scripts/e2e_test.py
```

## Key Implementation Details

### Producer
- Uses `schedule` library (implied from codebase context) to run every hour at :00
- Fetches from OpenWeather API with single location query
- Returns full JSON response object with nested `location` and `current` fields
- Publishes as string to RabbitMQ queue
- Logs on success/failure, continues on errors

### Consumer
- Establishes persistent RabbitMQ connection with prefetch_count=1 (sequential processing)
- Receives messages as delivery tuples with method, properties, body
- Parses JSON: if decode fails (malformed), NACK with requeue=False (discard)
- If valid, POSTs to API: if fails, NACK with requeue=True (retry later)
- If success, manual ACK
- Logs all operations

### API
- `POST /api/weather`: Accepts dict (not Pydantic schema), calls create_weather_record
- create_weather_record in crud.py implements **upsert pattern**:
  - Extracts location and condition info from nested structure
  - Calls get_or_create_location (upsert by lat/lon)
  - Calls get_or_create_condition (upsert by code)
  - **Checks if WeatherRecord exists** with same (location_id, condition_id, localtime_epoch)
  - If exists: **Updates** all current weather fields (temp, humidity, wind, etc.) + updated_at timestamp
  - If not exists: **Creates** new WeatherRecord with FKs + created_at timestamp
  - Composite index `idx_weather_upsert` optimizes the existence check
  - Commits and returns record
- Error handling: HTTPException with status_code and detail
- CORS: enabled for all origins (development)

**Why Upsert?** Prevents duplicate records when:
- Consumer retries failed API requests (network errors get requeued)
- Processing backlogs of messages (same observation processed multiple times)
- Any idempotency failures in the message pipeline

### Database
- Alembic tracks migrations in `alembic_version` table (single row, current revision)
- Initial migration creates 3 tables with indexes including deduplication
- Foreign keys: weather_records → locations, weather_records → weather_conditions
- Timestamps: created_at (immutable on create), updated_at (auto-updated on any change)
- **Upsert Index**: `idx_weather_upsert` on (location_id, condition_id, localtime_epoch) enables O(1) existence checks
- Connection pool: size=5, max_overflow=10, pool_pre_ping=True (verify before use)
- When same weather observation is processed again, only updated_at changes (not created_at)

## Testing Notes

**Test framework ready but no tests written yet**: pytest/httpx available in api/pyproject.toml dev dependencies.

To add tests:
```bash
cd src/api
uv run pytest                          # Run all
uv run pytest tests/test_endpoints.py  # Single file
uv run pytest -k test_create_weather   # By name
uv run pytest --cov                    # Coverage
```

## Important Implementation Patterns

1. **Configuration Pattern**: All settings inherit from `BaseSettings`, load from `.env`, have defaults
2. **Error Handling**: Producer logs and continues; Consumer distinguishes retry-worthy errors; API raises HTTPException
3. **Database Operations**: Always use CRUD functions, never raw SQL in routes
   - Location/Condition: upsert by natural key (coordinates, code)
   - Weather Records: **upsert by (location_id, condition_id, localtime_epoch)** to prevent duplicates
4. **Logging**: All services use `loguru` with custom format (colors, timestamps, level)
5. **Async Patterns**: Producer runs scheduled task loop; Consumer runs blocking AMQP loop; API is async but blocking on DB calls
6. **Idempotency**: Weather record upsert ensures the pipeline can safely retry any message without creating duplicates

## Docker & Deployment

**Multi-stage Dockerfile approach** (all 3 services):
- Base: `python:3.11-slim`
- Install `uv` in container
- Copy pyproject.toml, install with `uv pip install --system -e .`
- Copy source code
- API only: Custom entrypoint script that runs `alembic upgrade head` before uvicorn

**Docker Compose networking**:
- Custom bridge network: `weather-network`
- Service names are DNS hostnames (use `postgres` not `localhost` in container)
- API depends_on postgres with healthcheck (ensures DB ready before API starts)
- Consumer depends_on both rabbit-mq and api

**Persistent storage**:
- postgres service has volume mount `postgres-data:/var/lib/postgresql/data`
- Named volume persists across container restarts

## Troubleshooting Checklist

- **API won't start**: Check migrations ran (`SELECT * FROM alembic_version`), verify POSTGRES_* env vars match docker-compose
- **Consumer not processing**: Verify RabbitMQ is running, check RABBIT_HOST/QUEUE_NAME, look for JSON decode errors in logs
- **No data in DB**: Confirm producer is fetching (check logs at :00 minute mark), consumer is consuming (check logs), API responses are 201 (not errors)
- **Port conflicts**: Use `lsof -i :8000` or `docker ps` to see what's running
- **Database connection issues**: Ensure healthcheck passes (`docker compose ps`), use `pool_pre_ping` is enabled

## Dependencies & Tools

- **Package manager**: `uv` (installed in containers, use `uv run` and `uv sync` locally)
- **API framework**: FastAPI + uvicorn
- **ORM**: SQLAlchemy 2.0+ with Alembic migrations
- **Message queue**: RabbitMQ + pika client
- **Configuration**: Pydantic + pydantic-settings
- **Logging**: loguru
- **Database**: PostgreSQL 16 (Alpine)
- **HTTP**: requests (producer), httpx (for tests)
- **Linting**: ruff (api only, in dev deps)
