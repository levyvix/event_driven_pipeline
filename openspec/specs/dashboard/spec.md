# dashboard Specification

## Purpose
TBD - created by archiving change add-metabase-dashboard. Update Purpose after archive.
## Requirements
### Requirement: Metabase Service Integration
The system SHALL provide a Metabase BI service that connects to PostgreSQL and enables non-technical users to visualize weather data via dashboards and ad-hoc queries.

#### Scenario: Metabase container starts and connects to PostgreSQL
- **WHEN** user runs `docker compose up -d`
- **THEN** Metabase service (metabase container) starts successfully on port 3000
- **AND** Metabase auto-detects and connects to PostgreSQL database using environment variables
- **AND** database appears as "Weather DB" in Metabase's admin panel without manual configuration

#### Scenario: Admin user creation during initial setup
- **WHEN** user navigates to `http://localhost:3000` for the first time
- **THEN** Metabase welcome wizard prompts for admin email and password
- **AND** admin user is persisted and authenticated on subsequent logins

#### Scenario: Database schema is automatically introspected
- **WHEN** Metabase connects to PostgreSQL
- **THEN** all tables (locations, weather_conditions, weather_records) appear in the "Browse Data" section
- **AND** columns are correctly typed (numeric, text, timestamp)

### Requirement: Weather Timeline Dashboard
The system SHALL provide a pre-configured dashboard displaying weather observations over time.

#### Scenario: Weather records by timestamp
- **WHEN** user views the Weather Timeline dashboard
- **THEN** a line or area chart displays weather_records.created_at (x-axis) vs count of records (y-axis)
- **AND** data is aggregated by hour or day (user-selectable granularity in future)
- **AND** chart updates reflect all records currently in the database

#### Scenario: Location filter
- **WHEN** user views the Weather Timeline dashboard
- **THEN** a filter dropdown shows all unique location names
- **AND** selecting a location filters the timeline to show only records for that location

### Requirement: Weather Trends Dashboard
The system SHALL provide visualizations of temperature and humidity trends by location.

#### Scenario: Temperature trend line chart
- **WHEN** user views the Weather Trends dashboard
- **THEN** a line chart displays location (x-axis) vs average temperature (y-axis)
- **AND** one trend line per location (or user-selectable date range)
- **AND** title and axes are labeled clearly

#### Scenario: Humidity distribution
- **WHEN** user views the Weather Trends dashboard
- **THEN** a second chart displays humidity percentages
- **AND** chart shows current, minimum, and maximum humidity values per location

### Requirement: Data Freshness Monitoring
The system SHALL provide KPI cards displaying data health metrics.

#### Scenario: Record count KPI
- **WHEN** user views the Data Freshness dashboard
- **THEN** a large number card displays total count of weather_records in the database
- **AND** a second card shows count of records from the current hour (or last update batch)

#### Scenario: Latest update timestamp
- **WHEN** user views the Data Freshness dashboard
- **THEN** a card displays the most recent weather_records.updated_at timestamp
- **AND** timestamp is formatted for human readability (e.g., "2 hours ago" or "2024-11-20 15:30 UTC")

### Requirement: Ad-Hoc Query Support
The system SHALL allow non-technical users to write simple queries without SQL knowledge.

#### Scenario: Browse and filter data
- **WHEN** user clicks "Browse Data" in Metabase main menu
- **THEN** user can select a table (e.g., weather_records)
- **AND** user can apply filters (e.g., "temperature > 20") using visual query builder
- **AND** results display in table format with sorting and pagination

#### Scenario: Drill-down into a record
- **WHEN** user clicks a row in a Metabase query result
- **THEN** a detail panel shows all columns for that record
- **AND** user can click linked columns (e.g., location_id) to view related location record

### Requirement: Metabase Configuration via Environment Variables
The system SHALL load PostgreSQL connection credentials from environment variables.

#### Scenario: Connection string from .env
- **WHEN** Metabase container starts
- **THEN** it reads `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` from `.env` file (passed via docker-compose)
- **AND** no additional manual PostgreSQL configuration is required in Metabase UI

#### Scenario: Graceful fallback for missing credentials
- **WHEN** environment variables are missing or invalid
- **THEN** Metabase starts and presents connection setup UI
- **AND** user can enter credentials manually through the web interface
