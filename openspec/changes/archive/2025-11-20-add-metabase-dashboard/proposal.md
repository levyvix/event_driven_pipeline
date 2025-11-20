# Change: Add Metabase Dashboard for Weather Data Visualization

## Why
Currently, weather data persisted to PostgreSQL is only accessible via API queries. A visual dashboard enables stakeholders to explore trends, monitor data quality, and generate reports without requiring API knowledge. Metabase provides a low-code BI solution that connects directly to PostgreSQL and requires minimal infrastructure overhead.

## What Changes
- Add Metabase service to Docker Compose stack
- Expose Metabase dashboard at `http://localhost:3000`
- Configure automatic PostgreSQL database connection for Metabase
- Create dashboard displaying:
  - Weather observations over time (timeline chart)
  - Temperature/humidity trends by location (line charts)
  - Current weather snapshot (card metrics)
  - Data freshness and record counts (KPI cards)
- Document Metabase setup and dashboard creation steps
- Add `.env` configuration for Metabase admin credentials

## Impact
- **Affected specs**: New capability `dashboard` (visualization and reporting)
- **Affected code**:
  - `docker/docker-compose.yaml` (add metabase service)
  - `.env.example` (add METABASE_* variables)
  - `CLAUDE.md` (add Metabase setup instructions)
  - `README.md` (reference dashboard feature)
- **No breaking changes** to producer, consumer, or API services
- **Non-blocking**: Metabase service is independent; pipeline works without it
- **Dependencies**: Requires PostgreSQL to be running (already required)
