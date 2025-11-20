# Design: Metabase Integration

## Context
The event-driven weather pipeline persists data to PostgreSQL but lacks a visual interface for exploring trends and monitoring data quality. Metabase is a self-hosted BI tool that provides:
- Direct PostgreSQL connection (no ETL pipeline needed)
- Low-code dashboard creation (UI-driven, no SQL required for basic dashboards)
- Lightweight containerization (Metabase image ~600MB)
- Simple authentication and user management

## Goals
- Enable non-technical stakeholders to visualize weather data without API knowledge
- Monitor pipeline health (data freshness, record counts, processing completeness)
- Support ad-hoc queries and trend analysis
- Minimal operational overhead (single Docker container, no separate database required)

### Non-Goals
- Advanced analytics (Metabase is BI, not a data warehouse)
- Real-time streaming dashboards (Metabase queries PostgreSQL; update frequency depends on query schedule)
- Multi-tenancy or per-user data filtering (development deployment only)
- Embedding dashboards in external applications

## Decisions

### Why Metabase over Alternatives?
| Option | Pros | Cons | Choice |
|--------|------|------|--------|
| **Metabase** | Self-hosted, PostgreSQL native, low-code, good UX | No real-time streaming | ✓ Selected |
| Grafana | Excellent for metrics | Requires prometheus/influxdb setup | - |
| Superset | Powerful, self-hosted | Higher operational complexity | - |
| Tableau | Industry standard | Expensive, proprietary | - |

**Rationale**: Metabase is the lowest-effort solution that works with PostgreSQL directly and provides professional dashboards with minimal configuration.

### Database Credentials
- Metabase receives PostgreSQL credentials via environment variables
- Same connection string as API service (shared database, read-only queries)
- No additional database user needed; Metabase runs as `weather_user` (existing role)

### Dashboard Initialization
**Approach: Manual Setup** (not automated)
- Metabase runs with empty database on first startup
- Admin user created via web UI during initial setup
- Dashboards created through web UI (point-click, no declarative config)
- **Why**: Metabase's configuration format (H2 or PostgreSQL backend) is complex; UI setup is faster and more maintainable

**Future Enhancement**: Could automate via Metabase API (`POST /api/dashboard`) if dashboard definitions need to be version-controlled.

### Port and Networking
- Metabase service runs on `http://localhost:3000` (standard Metabase port)
- Docker Compose bridge network: Metabase connects to `postgres` hostname
- Exposed to host for development access (not for production)

### Authentication & Security
- Default Metabase admin user: created via web UI during first login
- Development deployment: single admin user, no role-based access control
- No HTTPS or SSO configured (development only)
- **Production consideration**: Enable LDAP/OIDC and run behind reverse proxy

## Risks & Trade-offs

| Risk | Mitigation |
|------|-----------|
| Metabase stores config in H2 file system database (not persistent across container restarts) | Add volume mount for H2 database directory or switch to PostgreSQL backend after initial setup |
| Dashboard definitions not version-controlled (UI-driven creation) | Document dashboard structure in README; future enhancement to export/version dashboard JSON |
| Queries can be CPU-intensive on large datasets | Add query caching; monitor performance as data grows |
| Admin credentials not pre-configured (manual UI setup required) | Document setup steps in CLAUDE.md; provide screenshot guide if needed |

## Migration Plan

### Phase 1: Infrastructure (Non-Breaking)
1. Add Metabase service to `docker-compose.yaml`
2. Add environment variables to `.env.example`
3. Update `CLAUDE.md` with Metabase startup instructions
4. Test local deployment: `docker compose up -d`

### Phase 2: Initial Setup (Manual)
1. Navigate to `http://localhost:3000`
2. Create admin user via welcome wizard
3. Connect to PostgreSQL database
4. Create sample dashboards (weather timeline, temperature trends, data freshness)

### Phase 3: Documentation (Post-Deployment)
1. Add dashboard screenshots to README
2. Document common queries and drill-down patterns
3. Record setup video or GIF if helpful

### Rollback
- Remove Metabase service from `docker-compose.yaml`
- No data loss (all state in PostgreSQL, Metabase is stateless)
- Existing API and pipeline continue unaffected

## Open Questions
1. **Initial dashboards**: Should we provide sample dashboard definitions (JSON export) or expect users to create them via UI?
   - *Assumption for now*: Document UI steps; can automate later via API
2. **Data retention**: Should Metabase query results be cached, or always fresh from PostgreSQL?
   - *Assumption for now*: Default caching behavior (Metabase caches for 1 hour); can tune in settings
3. **User management**: How many Metabase users? Just admin for development?
   - *Assumption for now*: Single admin user; multi-user setup deferred to production deployment
