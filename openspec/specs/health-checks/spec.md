# health-checks Specification

## Purpose
TBD - created by archiving change test-end-to-end-setup. Update Purpose after archive.
## Requirements
### Requirement: Service Health Check Endpoints
All services MUST provide health check endpoints that verify they are running and can access their dependencies.

#### Scenario: API health endpoint returns 200 OK
```
Given: API container is running
When: Test performs GET request to /health
Then: Response status is 200 OK
And: Response body is {"status": "ok"} or similar
And: This confirms API is running and PostgreSQL connection works
```

#### Scenario: RabbitMQ is accessible and queue exists
```
Given: RabbitMQ container is running
When: Test establishes pika connection to rabbit-mq:5672
And: Test verifies queue "weather" exists
Then:
  - Connection succeeds without timeout
  - Queue is accessible for publishing and consuming
  - Test can declare queue without errors
```

#### Scenario: PostgreSQL is accessible and database is ready
```
Given: PostgreSQL container is running
When: Test connects via psycopg to postgres:5432
And: Test executes SELECT 1
Then:
  - Connection succeeds with credentials from env vars
  - Database "weather_db" exists and is accessible
  - weather_records table exists and has correct schema
```

#### Scenario: Metabase is running and responding
```
Given: Metabase container is running
When: Test performs GET request to http://metabase:3000
Then:
  - Response status is 200 OK (or redirect to /setup if not configured)
  - Metabase application is responsive
  - Metabase can connect to PostgreSQL database
```

### Requirement: Health Check Automation
The system MUST provide automated health check validation as part of E2E testing.

#### Scenario: E2E test validates all services before pipeline test
```
Given: Developer runs E2E test suite
When: Test startup phase executes
Then: Test performs health checks in order: API → PostgreSQL → RabbitMQ → Metabase
And: If any check fails, test fails immediately with clear error message
And: Error message indicates which service failed and suggests resolution
```

#### Scenario: Health check failure messages guide troubleshooting
```
Given: A service health check fails
When: E2E test reports the failure
Then: Error message includes:
  - Which service failed (e.g., "RabbitMQ")
  - Why it failed (e.g., "Connection timeout at rabbit-mq:5672")
  - Suggested action (e.g., "Run: docker compose logs rabbit-mq")
  - Expected vs actual status
```

#### Scenario: Health checks respect configured hostnames and ports
```
Given: Services are running on non-standard hosts/ports
When: Health checks are configured via environment variables
Then:
  - POSTGRES_HOST, POSTGRES_PORT, RABBIT_HOST, API_URL, METABASE_URL env vars are respected
  - Health checks connect to configured endpoints
  - Default values work in docker-compose environment (postgres:5432, rabbit-mq:5672, etc.)
```

### Requirement: Service Startup Order Validation
Services MUST start in correct dependency order and each MUST be fully healthy before tests run.

#### Scenario: Dependent services wait for their dependencies
```
Given: docker-compose.yaml defines dependencies (e.g., api depends_on postgres, consumer depends_on api)
When: Containers are started via docker compose up -d
Then: Services start in correct order:
  1. postgres (no dependencies)
  2. rabbit-mq (no dependencies)
  3. api (waits for postgres healthcheck)
  4. metabase (waits for postgres healthcheck)
  5. consumer (waits for rabbit-mq and api to be healthy)
  6. producer (waits for rabbit-mq)
```

#### Scenario: Test waits for all services to be fully healthy
```
Given: Some containers are running but not yet healthy
When: E2E test runs
Then: Test waits up to 60 seconds for all services to pass health checks
And: Once all healthy, test proceeds with pipeline validation
And: If any service fails health check after 60s, test fails with timeout message
```

### Requirement: Container Startup Logging
Services MUST log their startup status and readiness in a way that aids debugging.

#### Scenario: Each service logs when it is ready
```
Given: A container is starting
When: Container application is ready to receive requests
Then: Service logs a clear message: "[SERVICE] is ready" or "[SERVICE] listening on port X"
And: This message appears in docker compose logs output
And: Developer can verify startup by checking logs: `docker compose logs -f api`
```

#### Scenario: Failed startup is clearly indicated in logs
```
Given: A service fails to start
When: Container initialization fails (e.g., DB connection failed)
Then: Service logs error message with:
  - What failed (e.g., "Failed to connect to PostgreSQL")
  - Why it failed (e.g., "Connection refused at postgres:5432")
  - What was expected (e.g., "Expected PostgreSQL at postgres:5432")
```
