# e2e-testing Specification

## Purpose
TBD - created by archiving change test-end-to-end-setup. Update Purpose after archive.
## Requirements
### Requirement: Full Pipeline E2E Test
The system MUST provide an automated test that validates the complete event-driven pipeline: Producer → RabbitMQ → Consumer → API → Database.

#### Scenario: Successful message processing through entire pipeline
```
Given: All Docker containers are running and healthy
When: A test message (sample weather JSON) is published to RabbitMQ queue "weather"
Then:
  - Consumer receives and processes the message within 30 seconds
  - Consumer forwards the message to API via HTTP POST /api/weather
  - API returns 201 Created response
  - Database contains exactly 1 new weather_record
  - Record fields match the input message (location coords, temperature, humidity, wind speed, etc.)
```

#### Scenario: Idempotent upsert on duplicate message
```
Given: A weather record exists in the database from a previous test
When: The same weather JSON is published to RabbitMQ again
Then:
  - Consumer processes the message
  - API returns 201 Created or 200 OK (upsert behavior)
  - Database still contains exactly 1 record (not 2)
  - Record's updated_at timestamp changed, but created_at did not
```

#### Scenario: Consumer timeout indicates pipeline failure
```
Given: All containers are running but consumer is stuck or unhealthy
When: A test message is published to RabbitMQ
And: No new record appears in database within 30 seconds
Then: Test fails with clear error message "Consumer did not process message in time"
And: Error message suggests checking consumer logs
```

### Requirement: E2E Test Framework Setup
The system MUST configure pytest to run E2E tests with proper fixtures, database isolation, and service dependencies.

#### Scenario: Pytest can run E2E tests without external setup
```
Given: Developer is in src/api directory
When: Developer runs `uv run pytest tests/test_e2e_pipeline.py -v`
Then:
  - Pytest discovers and runs all E2E test cases
  - Each test is isolated (no cross-test data contamination)
  - Tests output clear pass/fail for each stage (health → publish → poll → verify)
  - Full test suite completes in < 60 seconds
```

#### Scenario: Test fixtures provide clean database state
```
Given: A pytest test function needs a clean database
When: Test uses fixture that clears weather_records before and after
Then:
  - Previous test data does not interfere
  - New test data is isolated from other concurrent tests
  - Cleanup happens regardless of pass/fail
```

### Requirement: E2E Test Validation Coverage
The system MUST verify all critical data flows and API contract compliance during E2E testing.

#### Scenario: Test validates API returns correct status codes
```
Given: Consumer successfully processes a message
When: Consumer POSTs message to API
Then: Test verifies API response is 201 Created (or 200 OK if upsert)
And: Test verifies response includes created record ID
And: Test verifies response schema matches Pydantic model
```

#### Scenario: Test validates database record integrity
```
Given: A message was successfully processed
When: Test queries database for new record
Then: Record contains:
  - All input fields (location: lat, lon, name, country)
  - All weather fields (temp, humidity, wind_speed, condition)
  - Timestamps: created_at and updated_at in ISO 8601 format
  - Foreign keys: location_id and condition_id (non-null)
  - created_at ≤ updated_at
```

### Requirement: Standalone E2E Test Script
The system MUST provide a Python script for validating the pipeline before or alongside docker-compose startup.

#### Scenario: Developer can run E2E test as a standalone script
```
Given: All Docker containers are running
When: Developer runs `python scripts/e2e_test.py`
Then:
  - Script runs without requiring pytest installation
  - Script outputs human-readable status: "✓ API healthy", "✓ Consumer processed message", etc.
  - Script exits with code 0 on success, 1 on failure
  - Script completes within 60 seconds
```

#### Scenario: Standalone script detects missing dependencies gracefully
```
Given: Required environment (RabbitMQ, PostgreSQL) is not running
When: Developer runs `python scripts/e2e_test.py`
Then: Script fails with clear message indicating which service is unreachable
And: Script suggests: `docker compose up -d` to start services
```

