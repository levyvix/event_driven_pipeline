# Event-Driven Weather Pipeline

An event-driven architecture for collecting, processing, and storing weather data using Docker, RabbitMQ, PostgreSQL, and FastAPI.

## Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│   Producer   │────>│  RabbitMQ    │────>│   Consumer   │────>│  Weather API   │
│              │     │              │     │              │     │                │
│ Fetches data │     │ Message Queue│     │ Processes    │     │ FastAPI Server │
│ from OpenWX  │     │              │     │ messages     │     │ Stores in DB   │
└──────────────┘     └──────────────┘     └──────────────┘     └────────────────┘
                                                                        │
                                                                        v
                                                                 ┌────────────────┐
                                                                 │  PostgreSQL    │
                                                                 │                │
                                                                 │ Weather Data   │
                                                                 │ Locations      │
                                                                 │ Conditions     │
                                                                 └────────────────┘
```

## Project Structure

```
event_driven_pipeline/
├── docker/
│   └── docker-compose.yaml       # Services orchestration
├── src/
│   ├── producer/                 # OpenWeather data fetcher
│   │   ├── producer_app/
│   │   │   └── api_fetcher.py    # Fetches data and publishes to RabbitMQ
│   │   ├── pyproject.toml
│   │   └── Dockerfile-producer
│   ├── consumer/                 # RabbitMQ message processor
│   │   ├── consumer_app/
│   │   │   └── message_processor.py
│   │   ├── pyproject.toml
│   │   └── Dockerfile-consumer
│   ├── api/                      # FastAPI Weather API
│   │   ├── api_app/
│   │   │   ├── main.py           # FastAPI app and routes
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   ├── database.py       # Database connection
│   │   │   ├── crud.py           # Database operations
│   │   │   ├── schemas.py        # Pydantic schemas
│   │   │   └── config.py         # Configuration
│   │   ├── alembic/              # Database migrations
│   │   │   ├── versions/         # Migration files
│   │   │   ├── env.py
│   │   │   └── alembic.ini
│   │   ├── pyproject.toml
│   │   └── Dockerfile-api
│   └── .dockerignore
├── .env                          # Environment variables
└── README.md
```

## Services

### Producer
- **Purpose**: Fetches weather data from OpenWeather API
- **Output**: Publishes messages to RabbitMQ
- **Dockerfile**: `Dockerfile-producer`

### Consumer
- **Purpose**: Listens to RabbitMQ messages and processes them
- **Output**: Sends processed data to the Weather API
- **Dockerfile**: `Dockerfile-consumer`

### Weather API
- **Purpose**: FastAPI server that receives weather data and stores it in PostgreSQL
- **Port**: 8000
- **Endpoints**:
  - `POST /api/weather` - Create weather record
  - `GET /api/weather` - List all records with pagination
  - `GET /api/weather/{record_id}` - Get specific record
  - `GET /api/weather/location/{location_name}` - Get records by location
  - `GET /api/weather/location/{location_name}/latest` - Get latest record for location
  - `GET /health` - Health check
- **Dockerfile**: `Dockerfile-api`

### Database
- **Type**: PostgreSQL 16 (Alpine)
- **Port**: 5432
- **Database**: `weather_db`
- **User**: `weather_user`
- **Password**: `weather_password` (from environment)

### Message Queue
- **Type**: RabbitMQ
- **Port**: 5672 (AMQP), 15672 (Management)

### Dashboard (Optional)
- **Type**: Metabase (self-hosted BI tool)
- **Port**: 3000
- **Purpose**: Visualize weather data trends, monitor data freshness, and create ad-hoc queries without SQL
- **Start**: `docker compose up -d metabase`
- **Access**: http://localhost:3000
- **Status**: Optional—all data remains accessible via API queries regardless of Metabase
- **More info**: See [Metabase Dashboard section in CLAUDE.md](CLAUDE.md#metabase-dashboard-optional)

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- WeatherAPI.com API key (free tier available)

## Setup & Installation

### 1. Get a WeatherAPI.com API Key

Follow these steps to obtain a free API key from [weatherapi.com](https://www.weatherapi.com/):

1. **Visit the website**: Go to https://www.weatherapi.com/
2. **Sign up for free**: Click the "Sign Up" button in the top right
3. **Create account**: Fill in your email, password, and basic information
4. **Confirm email**: Check your email and click the confirmation link
5. **Get your API key**: After logging in, you'll see your API key on the dashboard. It's displayed prominently as a 32-character alphanumeric string
6. **Copy the key**: Click "Copy" next to your API key and save it securely

Your API key will look like: `abc123def456ghi789jkl012mno345p`

### 2. Environment Configuration

Create a `.env` file in the project root based on `.env.example`:

```bash
# Required: Your API key from weatherapi.com
API_KEY=your_api_key_here

# Optional: RabbitMQ host (default: localhost)
RABBIT_HOST=localhost

# Optional: RabbitMQ queue name (default: weather)
QUEUE_NAME=weather

# Optional: PostgreSQL host (default: localhost)
POSTGRES_HOST=localhost
```

**Quick setup**: Copy the example and fill in your API key:
```bash
cp .env.example .env
# Then edit .env and replace "xxx" with your actual API key
```

### 3. Start the Services

```bash
cd docker
docker compose up -d
```

This will start all services:
- PostgreSQL
- RabbitMQ
- Weather API
- Producer
- Consumer

**Important**: The API container automatically runs database migrations on startup via the entrypoint script, which executes `alembic upgrade head`.

### 4. Verify Services are Running

Check all containers:
```bash
docker compose ps
```

Verify API is responding:
```bash
curl http://localhost:8000/health
```

Check PostgreSQL has tables:
```bash
docker exec docker-postgres-1 psql -U weather_user -d weather_db -c "\dt"
```

Should show:
- `locations` - Weather location data
- `weather_conditions` - Weather condition types
- `weather_records` - Current weather measurements
- `alembic_version` - Migration tracking

## Database Schema

### Locations Table
```
id (PK) | name | region | country | lat | lon | tz_id | created_at | updated_at
```
Indexes: `name`, `(lat, lon)`, `(name, country)`

### Weather Conditions Table
```
id (PK) | code (UNIQUE) | text | icon | created_at | updated_at
```

### Weather Records Table
```
id (PK) | location_id (FK) | condition_id (FK) | localtime_epoch | localtime |
temp_c | temp_f | feelslike_c | feelslike_f | windchill_c | windchill_f |
heatindex_c | heatindex_f | dewpoint_c | dewpoint_f | wind_mph | wind_kph |
wind_degree | wind_dir | gust_mph | gust_kph | pressure_mb | pressure_in |
precip_mm | precip_in | humidity | cloud | vis_km | vis_miles | uv |
short_rad | diff_rad | dni | gti | is_day | created_at | updated_at
```
Indexes: `location_id`, `(location_id, created_at)`, `last_updated_epoch`, `created_at`, `(location_id, condition_id, localtime_epoch)`

## Data Deduplication (Upsert Pattern)

The API implements an **upsert pattern** for weather records to prevent duplicates when the same weather observation is processed multiple times.

### How It Works

- Each weather observation is uniquely identified by: `(location_id, condition_id, localtime_epoch)`
- When a new weather message arrives:
  - **If matching record exists**: Updates all weather fields and timestamps
  - **If no match found**: Creates a new record
- The composite index `idx_weather_upsert` on `(location_id, condition_id, localtime_epoch)` ensures fast lookup

### Benefits

- **Prevents duplicates** from consumer retries or message requeuing
- **Handles backlog processing** safely (no explosion of records)
- **Updates stale data** if the same observation is reprocessed with new values
- **Maintains data integrity** - `created_at` timestamp never changes, `updated_at` is set on updates

### Example Scenario

1. Producer publishes weather observation for Vila Velha at epoch 1763649094
2. Consumer sends to API → **Creates record ID 1**
3. If consumer retries (network error) → **Updates record ID 1** (not duplicated)
4. If backlog of 100 messages with same timestamp → **Only 1 record** (all updates to the same record)

### Implementation Details

See `src/api/api_app/crud.py` function `create_weather_record()` for the upsert logic.

## Database Migrations

### How It Works

1. **Alembic** is used for database version control
2. Migration files are stored in `src/api/alembic/versions/`
3. On API startup, the entrypoint script runs: `alembic upgrade head`
4. This automatically applies any pending migrations

### Current Migrations

- `840dc0f71a0e_initial_migration_with_all_tables_and_indexes.py` - Creates all base tables with deduplication index

### Creating New Migrations

If you modify the models in `src/api/api_app/models.py`, generate a new migration:

```bash
cd src/api
uv run alembic revision --autogenerate -m "Description of changes"
```

Then apply it:
```bash
uv run alembic upgrade head
```

## API Usage Examples

### Create a Weather Record
```bash
curl -X POST http://localhost:8000/api/weather \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": 1,
    "condition_id": 1,
    "localtime_epoch": 1234567890,
    "localtime": "2025-11-20 12:00:00",
    ...
  }'
```

### List All Weather Records
```bash
curl http://localhost:8000/api/weather?page=1&page_size=50
```

### Get Latest Weather for Location
```bash
curl http://localhost:8000/api/weather/location/New%20York/latest
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Development

### Local Setup (Without Docker)

1. Install dependencies for each service:
```bash
cd src/api && uv sync
cd ../producer && uv sync
cd ../consumer && uv sync
```

2. Start PostgreSQL and RabbitMQ using Docker only:
```bash
docker compose up postgres rabbit-mq -d
```

3. Run services locally:
```bash
# Terminal 1 - API
cd src/api
uv run uvicorn api_app.main:app --reload

# Terminal 2 - Producer
cd src/producer
uv run python -m producer_app.api_fetcher

# Terminal 3 - Consumer
cd src/consumer
uv run python -m consumer_app.message_processor
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is healthy: `docker compose ps`
- Check logs: `docker compose logs postgres`
- Verify database exists: `docker exec docker-postgres-1 psql -U weather_user -l`

### RabbitMQ Issues
- Check RabbitMQ logs: `docker compose logs rabbit-mq`
- Access management UI: http://localhost:15672 (guest/guest)

### API Not Starting
- Check if port 8000 is available
- View logs: `docker compose logs api`
- Verify migrations ran: `docker exec docker-postgres-1 psql -U weather_user -d weather_db -c "SELECT * FROM alembic_version;"`

### No Data in Database
- Verify consumer is running: `docker compose logs consumer`
- Check producer has valid `API_KEY` set in `.env` (get it from https://www.weatherapi.com/)
- View consumer logs for errors processing messages
- Test API directly: `curl -X GET http://localhost:8000/api/weather`

## Cleaning Up

Stop all services:
```bash
docker compose down
```

Remove volumes (clears database):
```bash
docker compose down -v
```

Restart fresh:
```bash
docker compose down -v
docker compose up -d
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | **Required** | API key from [weatherapi.com](https://www.weatherapi.com/) |
| `RABBIT_HOST` | `localhost` / `rabbit-mq` | RabbitMQ host (localhost for local dev, rabbit-mq in Docker) |
| `QUEUE_NAME` | `weather` | RabbitMQ queue name |
| `POSTGRES_HOST` | `localhost` / `postgres` | Database host (localhost for local dev, postgres in Docker) |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_USER` | `weather_user` | Database user |
| `POSTGRES_PASSWORD` | `weather_password` | Database password |
| `POSTGRES_DB` | `weather_db` | Database name |
| `API_URL` | `http://api:8000/api/weather` | API endpoint for consumer (in Docker) |
