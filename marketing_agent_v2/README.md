# Marketing Agent V2

A **production-ready, human-in-the-loop marketing automation platform** built with modern microservices architecture. Version 2 prioritizes **scalability, auditability, and human control** over full autonomy.

## Key Features

| Feature | Description |
| :--- | :--- |
| **Human-in-the-Loop Workflow** | All outbound actions require explicit approval before execution. Includes a KILL_SWITCH for emergency control. |
| **Advanced Link Tracking** | Internal short-link service (`/r/{slug}`) with detailed click analytics (device type, geo-location, bot filtering). |
| **Trend Engine** | RSS feed ingestion with velocity-based trend scoring and automated digest generation. |
| **Execution Connectors** | Pluggable connectors for Email (SendGrid), Social Media (Buffer), and CMS (webhooks) with mock modes. |
| **Audit Trail** | Complete audit logging of all system events for compliance and debugging. |
| **Admin Dashboard** | Minimal but functional web UI for managing approvals, trends, and campaigns. |
| **Microservices Architecture** | FastAPI (API), Celery (Worker), PostgreSQL (DB), Redis (Broker) via Docker Compose. |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│  (/api/campaigns, /api/links, /api/actions, /admin)         │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
   │PostgreSQL│      │  Redis  │     │ Celery  │
   │   (DB)   │      │ (Broker)│     │ (Worker)│
   └──────────┘      └─────────┘     └────┬────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
                   │  Email   │        │  Social  │        │   CMS    │
                   │Connector │        │Connector │        │Connector │
                   └──────────┘        └──────────┘        └──────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

### 1. Clone and Setup

```bash
cd /path/to/marketing_agent_v2
cp .env.example .env
```

### 2. Start Services

```bash
# Using Docker Compose
docker-compose up -d

# Or using Make
make up
```

The system will start with:
- **API**: http://localhost:8000
- **Admin Dashboard**: http://localhost:8000/admin
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 3. Run Migrations

```bash
# Using Make
make migrate

# Or manually
docker-compose exec api alembic upgrade head
```

### 4. Demo Workflow

```bash
# Ingest trends from RSS feeds
curl -X POST http://localhost:8000/api/trends/ingest

# Create a campaign
curl -X POST http://localhost:8000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Campaign",
    "objective": "Test marketing automation",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-12-31T23:59:59"
  }'

# Create a tracked link
curl -X POST http://localhost:8000/api/links \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "channel": "email",
    "long_url": "https://example.com/landing"
  }'

# Create an email action
curl -X POST http://localhost:8000/api/actions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "payload": {
      "recipient": "user@example.com",
      "subject": "Check out our new product",
      "body": "We have something exciting for you!"
    },
    "dry_run": false
  }'

# Submit for approval
curl -X POST http://localhost:8000/api/actions/1/submit

# Approve the action
curl -X POST http://localhost:8000/api/actions/1/approve \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "note": "Looks good!"}'
```

## API Endpoints

### Health & Status
- `GET /healthz` - Health check

### Campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{id}` - Get campaign
- `PUT /api/campaigns/{id}` - Update campaign

### Links & Tracking
- `POST /api/links` - Create tracked link
- `GET /api/links` - List links
- `GET /api/links/{id}` - Get link details
- `GET /api/links/{id}/stats` - Get link statistics
- `GET /r/{slug}` - Redirect short link (records click)

### Trends
- `POST /api/trends/ingest` - Manually trigger trend ingestion
- `GET /api/trends/digest` - Get trend digest

### Actions & Approvals
- `POST /api/actions` - Create action
- `GET /api/actions` - List actions
- `GET /api/actions/{id}` - Get action
- `POST /api/actions/{id}/submit` - Submit for approval
- `POST /api/actions/{id}/approve` - Approve action
- `POST /api/actions/{id}/deny` - Deny action

### Admin UI
- `GET /admin` - Dashboard
- `GET /admin/approvals` - Approvals page
- `GET /admin/trends` - Trends page
- `GET /admin/links` - Links page
- `GET /admin/campaigns` - Campaigns page

## Configuration

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://marketing_user:marketing_password@postgres:5432/marketing_db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `KILL_SWITCH` | Emergency stop for all actions | `false` |
| `SENDGRID_API_KEY` | SendGrid API key (optional) | - |
| `BUFFER_TOKEN` | Buffer API token (optional) | - |
| `BITLY_TOKEN` | Bitly API token (optional) | - |
| `CMS_WEBHOOK_URL` | CMS webhook URL (optional) | - |

### RSS Feeds Configuration

Edit `config/feeds.yaml` to configure RSS feeds for trend ingestion:

```yaml
feeds:
  - name: "HackerNews"
    url: "https://news.ycombinator.com/rss"
  - name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
  - name: "ProductHunt"
    url: "https://www.producthunt.com/feed"
```

## Development

### Make Commands

```bash
make up              # Start all services
make down            # Stop all services
make migrate         # Run database migrations
make test            # Run tests
make lint            # Run linting
make logs            # View logs
make shell           # Open shell in API container
make seed            # Seed database with sample data
make demo            # Run demo workflow
```

### Running Tests

```bash
# Using Make
make test

# Or directly
docker-compose exec api pytest tests/ -v
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec api alembic revision --autogenerate -m "Add new column"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback
docker-compose exec api alembic downgrade -1
```

## Data Models

### Core Tables

| Table | Purpose |
| :--- | :--- |
| `users` | User accounts with roles (admin, editor, viewer) |
| `campaigns` | Marketing campaigns |
| `assets` | Content assets (images, text, etc.) |
| `links` | Tracked short links with UTM parameters |
| `click_events` | Click events with device/geo/bot info |
| `trend_items` | RSS feed items |
| `trend_scores` | Computed trend scores |
| `actions` | Outbound marketing actions (email, social, cms) |
| `approvals` | Action approvals with audit trail |
| `audit_logs` | Complete system event log |

## Workflow: Creating and Executing an Action

1. **Create Action** (Draft)
   ```
   POST /api/actions
   ```

2. **Submit for Approval** (Pending Approval)
   ```
   POST /api/actions/{id}/submit
   ```

3. **Approve Action** (Approved)
   ```
   POST /api/actions/{id}/approve
   ```

4. **Worker Executes** (Executing → Succeeded/Failed)
   - Worker polls for approved actions
   - Checks KILL_SWITCH
   - Calls appropriate connector
   - Updates status and audit log

## Bot Detection

The system detects bot traffic by checking:
- User agent for bot tokens (bot, spider, crawl, slurp, etc.)
- Missing user agent + empty referrer (suspicious)
- Common bot user agents (Googlebot, Bingbot, etc.)

Detected bots are marked with `is_bot=true` in click events but still counted in analytics.

## Trend Scoring Algorithm

Trends are scored based on **velocity** (mentions in last 24h / mentions in previous 24-72h):

- **Velocity > 3x**: "Rapidly trending"
- **Velocity > 1.5x**: "Trending"
- **Velocity ≤ 1.5x**: "Emerging"

## Execution Connectors

### Email Connector
- **Real**: SendGrid (if `SENDGRID_API_KEY` set)
- **Mock**: Logs to stdout and audit log

### Social Connector
- **Real**: Buffer (if `BUFFER_TOKEN` set)
- **Mock**: Logs to stdout and audit log

### CMS Connector
- **Real**: Generic webhook (if `CMS_WEBHOOK_URL` set)
- **Mock**: Logs to stdout and audit log

All connectors support:
- Dry-run mode (no actual execution)
- Retry logic with exponential backoff
- Idempotency (no duplicate execution)

## Scheduled Tasks

The Celery Beat scheduler runs:

| Task | Schedule | Purpose |
| :--- | :--- | :--- |
| `ingest_trends` | Daily at 00:00 UTC | Ingest RSS feeds |
| `compute_trend_scores` | Daily at 01:00 UTC | Compute trend scores |
| `execute_pending_actions` | Every 5 minutes | Execute approved actions |

## Monitoring & Logging

- **Application Logs**: `docker-compose logs api`
- **Worker Logs**: `docker-compose logs worker`
- **Scheduler Logs**: `docker-compose logs scheduler`
- **Audit Trail**: Query `audit_logs` table for all events

## Production Deployment

### Recommended Setup

1. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
2. **Redis**: Use managed Redis (AWS ElastiCache, etc.)
3. **Hosting**: Deploy with Kubernetes or Docker Swarm
4. **Monitoring**: Add Prometheus + Grafana for metrics
5. **Logging**: Centralize logs with ELK or Datadog

### Security Considerations

- Change `SECRET_KEY` in production
- Use environment variables for all secrets
- Enable SSL/TLS for all connections
- Implement rate limiting on API endpoints
- Use database connection pooling
- Enable audit logging for compliance

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Verify database connectivity
docker-compose exec api python -c "from app.database import engine; engine.connect()"
```

### Migrations fail
```bash
# Check migration status
docker-compose exec api alembic current

# Rollback and retry
docker-compose exec api alembic downgrade -1
docker-compose exec api alembic upgrade head
```

### Worker not executing actions
```bash
# Check worker logs
docker-compose logs worker

# Verify Redis connectivity
docker-compose exec redis redis-cli ping
```

## Next Steps

1. Configure external API keys in `.env`
2. Customize RSS feeds in `config/feeds.yaml`
3. Implement custom connectors as needed
4. Deploy to production infrastructure
5. Set up monitoring and alerting

## Support & Contributing

For issues, feature requests, or contributions, please refer to the project documentation or contact the development team.

---

**Version**: 2.0.0  
**Last Updated**: December 2025  
**Status**: Production Ready
