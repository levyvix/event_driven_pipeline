# Project Context

## Purpose
Event-Driven Weather Pipeline: A 5-layer system that fetches weather data hourly from OpenWeather API, processes it asynchronously through a message queue, validates and deduplicates it, and persists it to a database. The system demonstrates real-time event processing with guaranteed message delivery and idempotent data handling.

## Tech Stack
- **Language**: Python 3.11
- **API Framework**: FastAPI + uvicorn
- **Message Queue**: RabbitMQ 4.0+
- **ORM**: SQLAlchemy 2.0+ with Alembic migrations
- **Database**: PostgreSQL 16 (Alpine)
- **Configuration**: Pydantic + pydantic-settings
- **Logging**: loguru
- **HTTP**: requests (producer), httpx (tests)
- **Package Manager**: uv (universal Python installer)
- **Dev Tools**: pytest, ruff linter
- **Containerization**: Docker + Docker Compose

## Project Conventions

### Code Style
- **Python**: Follow PEP 8 conventions; formatting enforced by ruff linter (api service)
- **Naming**: snake_case for functions/variables, PascalCase for classes and Pydantic models
- **Imports**: Standard library → third-party → local (organized by tool like isort)
- **Type Hints**: Use type hints on all function signatures for clarity
- **Docstrings**: Add only when logic isn't self-evident; keep comments minimal
- **Constants**: UPPERCASE for configuration constants (used minimally; Pydantic Settings preferred)

### Architecture Patterns
- **Producer-Consumer Pattern**: Decoupled data ingestion (Producer) from processing (Consumer) via RabbitMQ
- **Upsert Pattern**: Database records deduplicated by natural keys (location: lat/lon, condition: code, weather: location_id + condition_id + localtime_epoch)
- **Configuration Pattern**: All settings inherit from `BaseSettings`, load from `.env`, have sensible defaults
- **CRUD Layer**: All database operations abstracted in `crud.py`; never raw SQL in routes
- **Error Handling**:
  - Producer: logs and continues on errors (resilient ingestion)
  - Consumer: distinguishes retry-worthy errors (NACK with requeue=True) from permanent failures (NACK with requeue=False)
  - API: raises HTTPException with status_code and detail
- **Idempotency**: Weather record upsert ensures pipeline can safely retry any message without creating duplicates
- **Logging**: All services use loguru with custom format (colors, timestamps, level)
- **Async Patterns**: Producer runs scheduled task loop; Consumer runs blocking AMQP loop; API is async but blocking on DB calls

### Testing Strategy
- **Framework**: pytest + httpx (available in api/pyproject.toml dev dependencies)
- **Current Status**: Test framework ready but no tests written yet
- **Expected Coverage**: Unit tests for CRUD operations, integration tests for API endpoints, payload validation tests
- **Manual Testing Approach**: Full pipeline tested via docker-compose (producer → queue → consumer → API → DB)
- **To Run Tests**:
  ```bash
  cd src/api
  uv run pytest                          # Run all
  uv run pytest tests/test_endpoints.py  # Single file
  uv run pytest -k test_create_weather   # By name
  uv run pytest --cov                    # Coverage report
  ```

### Git Workflow
- **Branches**: Feature work on feature branches; PRs to main before merge
- **Commit Messages**: Present tense, descriptive ("feat: Add new endpoint" not "Added endpoint")
- **Conventional Commits** (implied from existing commits):
  - `feat:` for new features
  - `fix:` for bug fixes
  - `refactor:` for code restructuring without behavior change
  - `docs:` for documentation updates
  - `test:` for test additions/modifications
  - Include scope if helpful: `feat(producer): Add retry logic`

## Domain Context

### Weather Data Model
- **Source**: OpenWeather API (current weather endpoint)
- **Input Structure**: Nested JSON with `location` object (lat, lon, name, country) and `current` object (temp, feels_like, humidity, wind_speed, condition_code, condition_description, localtime_epoch)
- **Deduplication Key**: Weather observation uniqueness determined by (location_id, condition_code, localtime_epoch) tuple
- **Update Semantics**: When same observation processed again, all current weather fields updated but created_at preserved

### Queue Configuration
- **Queue Name**: "weather" (configurable via `QUEUE_NAME` env var)
- **Consumer Prefetch**: prefetch_count=1 (sequential processing, manual ACK)
- **Message Format**: Raw JSON string from producer
- **ACK Handling**: Manual ACK on successful API POST; NACK+requeue on network errors; NACK+discard on malformed JSON

### API Contract
- **Endpoint**: `POST /api/weather` accepts raw dict (not strict Pydantic schema) for flexibility with OpenWeather API changes
- **Idempotency**: Same POST request is safe to retry (upsert semantics)
- **Database Indexes**: Composite index `idx_weather_upsert` on (location_id, condition_id, localtime_epoch) for O(1) upsert checks

## Important Constraints
- **Single Location**: Producer fetches weather for one hardcoded location (configurable via API key only; not location parameterized yet)
- **Hourly Schedule**: Producer runs exactly on :00 minute mark (scheduled, not triggered)
- **Manual ACK Model**: RabbitMQ requires explicit ACK from consumer; network/parsing errors must be distinguished
- **Stateless Services**: Each service is ephemeral; state persists only in RabbitMQ and PostgreSQL
- **No Authentication**: API has no auth layer (development only; CORS enabled for all origins)
- **Blocking DB Calls**: API is async FastAPI but DB calls block event loop (migration from sync drivers not prioritized)

## External Dependencies
- **OpenWeather API**: Requires `OPENWEATHER_API_KEY` env var; provides weather data endpoint
- **RabbitMQ**: Message broker for queue "weather"; must be running and accessible at `RABBIT_HOST` (default: localhost:5672)
- **PostgreSQL**: Persists location, condition, and weather_record tables; requires credentials via env vars
- **Docker Compose**: Orchestrates all services locally (postgres, rabbit-mq, api, consumer, producer)
- **Python Package Registry**: uv installs dependencies from PyPI
