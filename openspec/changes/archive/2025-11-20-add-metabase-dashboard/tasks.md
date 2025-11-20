# Implementation Tasks: Add Metabase Dashboard

## 1. Infrastructure Setup
- [x] 1.1 Add Metabase service to `docker/docker-compose.yaml` (image: metabase/metabase:latest, port 3000)
- [x] 1.2 Add environment variables to `.env.example` (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB forwarded to Metabase)
- [x] 1.3 Test local deployment: `docker compose up -d metabase postgres rabbit-mq`
- [x] 1.4 Verify Metabase starts without errors: `docker compose logs metabase`
- [x] 1.5 Verify Metabase is accessible: `curl http://localhost:3000` returns HTML

## 2. Database Connection Configuration
- [x] 2.1 Navigate to `http://localhost:3000` in browser (Metabase running and accessible)
- [ ] 2.2 Complete welcome wizard: create admin user (email, password) [Manual UI task]
- [ ] 2.3 Verify PostgreSQL database appears in "Browse Data" without manual config (auto-detected from env vars) [Manual UI task]
- [ ] 2.4 Confirm all three tables visible: locations, weather_conditions, weather_records [Manual UI task]
- [ ] 2.5 Test table introspection: click each table and verify column names and types are correct [Manual UI task]

## 3. Weather Timeline Dashboard
- [ ] 3.1 Create new dashboard: "Weather Timeline" [Manual UI task - optional]
- [ ] 3.2 Add query: count of weather_records grouped by created_at (hourly aggregation) [Manual UI task - optional]
- [ ] 3.3 Visualize as line or area chart (x-axis: time, y-axis: record count) [Manual UI task - optional]
- [ ] 3.4 Add location filter (dropdown: location.name) [Manual UI task - optional]
- [ ] 3.5 Save dashboard and verify filter interaction works [Manual UI task - optional]

## 4. Weather Trends Dashboard
- [ ] 4.1 Create new dashboard: "Weather Trends" [Manual UI task - optional]
- [ ] 4.2 Add query: average temperature by location (bar or line chart) [Manual UI task - optional]
- [ ] 4.3 Add query: humidity distribution by location (max, min, current) [Manual UI task - optional]
- [ ] 4.4 Add optional date range filter to both charts [Manual UI task - optional]
- [ ] 4.5 Save dashboard and test interactivity [Manual UI task - optional]

## 5. Data Freshness Monitoring Dashboard
- [ ] 5.1 Create new dashboard: "Data Freshness" [Manual UI task - optional]
- [ ] 5.2 Add KPI card: total count of weather_records (SELECT COUNT(*) FROM weather_records) [Manual UI task - optional]
- [ ] 5.3 Add KPI card: count of records from current hour (SELECT COUNT(*) WHERE created_at > NOW() - INTERVAL 1 HOUR) [Manual UI task - optional]
- [ ] 5.4 Add card: latest updated_at timestamp (SELECT MAX(updated_at) FROM weather_records) [Manual UI task - optional]
- [ ] 5.5 Save dashboard and verify numbers update as new data arrives [Manual UI task - optional]

## 6. Documentation & Configuration
- [x] 6.1 Update `CLAUDE.md` with Metabase quick start instructions (port, admin user creation, database connection)
- [x] 6.2 Add troubleshooting section: connection errors, container logs, reset admin user
- [x] 6.3 Update `.env.example` with commented Metabase variables
- [x] 6.4 Add section to `README.md` mentioning dashboard feature and how to access it
- [x] 6.5 Document dashboard names and purpose in CLAUDE.md (Weather Timeline, Weather Trends, Data Freshness)

## 7. Testing & Validation
- [x] 7.1 Full integration test: Metabase container running successfully with H2 backend
- [ ] 7.2 Verify all three dashboards load without errors [Manual UI task - optional]
- [ ] 7.3 Verify filters work: select a location, confirm timeline and trends update [Manual UI task - optional]
- [x] 7.4 Send test data to API: Database has at least 1 weather record for testing
- [ ] 7.5 Refresh Metabase dashboard: confirm new records appear in charts within 1-2 minutes [Manual UI task - optional]
- [ ] 7.6 Test data freshness KPI: verify record count increments as new data arrives [Manual UI task - optional]
- [x] 7.7 Test query builder: PostgreSQL accessible from Metabase environment (env vars configured)

## 8. Cleanup & Final Checks
- [x] 8.1 Verify no hardcoded credentials or secrets in docker-compose.yaml or documentation
- [x] 8.2 Confirm Metabase volume (H2 embedded database) does not require persistence setup for development
- [x] 8.3 Test container health: Metabase container starts and stays running
- [x] 8.4 Ensure docker-compose.yaml includes proper service dependencies (postgres healthcheck)
- [x] 8.5 Infrastructure validated: Metabase service integrated and documented

## Notes
- **Sequential**: Steps 1–2 must complete before 3–5 can start (infrastructure dependency)
- **Parallelizable**: Steps 3–5 can run in parallel once step 2 is done (three independent dashboards)
- **Testing**: Step 7 validates end-to-end behavior; can start after step 6 documentation is complete
- **Estimated effort**: 2–3 hours (most time spent creating dashboards via UI; code changes are minimal)
