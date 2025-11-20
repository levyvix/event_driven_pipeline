# Proposal: End-to-End Testing from Zero Setup

**Change ID**: `test-end-to-end-setup`

**Author**: Claude Code

**Status**: Proposal

**Summary**: Add automated end-to-end testing to verify that a fresh clone of the repository can be set up and run successfully, with all services (API, Producer, Consumer, RabbitMQ, PostgreSQL, Metabase) functioning correctly and demonstrating the full event-driven pipeline (Producer → RabbitMQ → Consumer → API with 201 Created response).

## Problem Statement

Currently, there is no automated verification that the project runs successfully from a fresh clone. A developer following the documentation should see:
1. All Docker containers starting without errors
2. The Producer publishing messages to RabbitMQ
3. The Consumer receiving messages and forwarding them to the API
4. The API returning 201 Created status codes on successful record creation
5. Metabase responding and ready to visualize data

Without end-to-end testing, regressions in setup, configuration, or service integration can go undetected.

## Goals

1. **Zero-Setup Confidence**: Enable anyone to clone the repo, follow documentation, and verify success
2. **Automated Pipeline Validation**: Confirm Producer → RabbitMQ → Consumer → API flow works end-to-end
3. **Health Checks**: Ensure all services (including Metabase) start cleanly and are responsive
4. **Database Verification**: Verify that data flows through the entire pipeline and persists correctly
5. **Documentation Reliability**: Detect documentation gaps or outdated instructions

## Scope

### In Scope
- Health check endpoints for all services (API, RabbitMQ, PostgreSQL, Metabase)
- E2E test script that validates full pipeline: Producer → Queue → Consumer → API → Database
- Verification of 201 Created response from API
- Metabase readiness check (HTTP 200 and connectivity to PostgreSQL)
- Documentation of how to run tests from a fresh clone
- Automated test runner (Python script or shell script callable from CI/CD)

### Out of Scope
- Unit tests for individual functions
- Performance/load testing
- Security testing
- Visual regression testing on Metabase dashboards
- Modifying the core event pipeline logic

## Proposed Changes

### 1. **E2E Testing Capability** (`specs/e2e-testing/spec.md`)
- Add pytest-based E2E tests in `src/api/tests/test_e2e_pipeline.py`
- Test validates: Producer message → Queue → Consumer → API 201 response → Database record

### 2. **Health Checks & Service Readiness** (`specs/health-checks/spec.md`)
- Extend API with `/health` endpoint (already exists per CLAUDE.md)
- Add RabbitMQ health check via pika connection test
- Add PostgreSQL health check (already exists via docker healthcheck)
- Add Metabase health check endpoint verification (HTTP GET to port 3000)
- Document service startup order and dependencies

### 3. **Documentation Updates** (`CLAUDE.md`)
- Add "E2E Testing" section with quick-start commands
- Document expected output for successful pipeline run
- Troubleshooting guide for common setup failures

## Design Rationale

- **E2E Over Unit Tests First**: The primary concern is pipeline integrity, not individual function correctness. Testing the full flow first builds confidence.
- **Health Checks**: Distributed system debugging is hard; health checks make it obvious which service failed.
- **Pytest**: Aligns with existing test framework in `api/pyproject.toml`.
- **Python Script Option**: Provides fallback for environments without pytest installed during initial setup.

## Success Criteria

1. A developer can run a single command after `docker compose up -d` to verify the entire pipeline works
2. Test output clearly indicates which step failed (Producer, RabbitMQ, Consumer, API, Database, Metabase)
3. Test passes within 60 seconds of all containers being healthy
4. Documented in `CLAUDE.md` with examples
5. All services respond without errors

## Timeline Estimation

- Health checks & documentation: 1-2 hours
- E2E test script: 2-3 hours
- Documentation updates & validation: 1 hour
- Total: 4-6 hours
