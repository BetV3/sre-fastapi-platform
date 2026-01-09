# FastAPI Platform

Production-ready FastAPI boilerplate with full observability stack.

## Features

- **FastAPI Application**: Async Python API with structured logging, health checks, and metrics
- **Redis**: Caching and session storage
- **Prometheus**: Metrics collection and alerting rules
- **Grafana**: Dashboards and visualization
- **Loki**: Log aggregation
- **Promtail**: Log shipping from Docker containers
- **Alertmanager**: Alert routing and notification

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start all services
make docker-up

# Or manually
docker compose up -d
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
make dev

# Run the application
make run
```

## Services

| Service      | URL                     | Description              |
|-------------|-------------------------|--------------------------|
| API         | http://localhost:8000   | FastAPI application      |
| API Docs    | http://localhost:8000/docs | Swagger UI            |
| Prometheus  | http://localhost:9090   | Metrics & queries        |
| Grafana     | http://localhost:3000   | Dashboards (admin/admin) |
| Alertmanager| http://localhost:9093   | Alert management         |
| Loki        | http://localhost:3100   | Log queries              |
| Redis       | localhost:6379          | Cache/session store      |

## API Endpoints

- `GET /` - Root endpoint with app info
- `GET /api/v1/health` - Detailed health check
- `GET /api/v1/health/live` - Kubernetes liveness probe
- `GET /api/v1/health/ready` - Kubernetes readiness probe
- `GET /metrics` - Prometheus metrics
- `GET /api/v1/items` - List items (example CRUD)
- `POST /api/v1/items` - Create item
- `GET /api/v1/items/{id}` - Get item
- `PUT /api/v1/items/{id}` - Update item
- `DELETE /api/v1/items/{id}` - Delete item

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/              # API version 1 routes
│   ├── core/                # Core utilities
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── logging.py       # Structured logging
│   │   ├── metrics.py       # Prometheus metrics
│   │   ├── middleware.py    # Custom middleware
│   │   └── redis.py         # Redis client
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   ├── config.py            # Settings management
│   ├── dependencies.py      # FastAPI dependencies
│   └── main.py              # Application entry point
├── config/
│   ├── alertmanager/        # Alertmanager config
│   ├── grafana/             # Grafana provisioning & dashboards
│   ├── loki/                # Loki config
│   ├── prometheus/          # Prometheus config & alert rules
│   └── promtail/            # Promtail config
├── tests/                   # Test files
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Multi-stage Dockerfile
├── Makefile                 # Development commands
├── pyproject.toml           # Python project config
└── requirements.txt         # Python dependencies
```

## Configuration

Environment variables can be set in `.env` file (copy from `.env.example`):

| Variable           | Default                | Description                |
|-------------------|------------------------|----------------------------|
| `APP_NAME`        | FastAPI Platform       | Application name           |
| `ENVIRONMENT`     | development            | Environment (dev/staging/prod) |
| `DEBUG`           | false                  | Debug mode                 |
| `LOG_LEVEL`       | INFO                   | Logging level              |
| `LOG_FORMAT`      | json                   | Log format (json/text)     |
| `REDIS_URL`       | redis://redis:6379/0   | Redis connection URL       |
| `METRICS_ENABLED` | true                   | Enable Prometheus metrics  |

## Development

```bash
# Run tests
make test

# Run linter
make lint

# Format code
make format

# Type checking
make typecheck

# Clean build artifacts
make clean
```

## Monitoring

### Grafana

Access Grafana at http://localhost:3000 (default credentials: admin/admin).

Pre-configured dashboards:
- **FastAPI Overview**: Request rates, latencies, error rates, and logs

### Prometheus Alerts

Pre-configured alerts:
- High error rate (>5%)
- High latency (p95 > 1s)
- Application down
- Low request rate

### Viewing Logs

1. Open Grafana
2. Go to Explore → Select Loki
3. Query: `{job="api"}`

## Production Considerations

1. **Security**:
   - Change default Grafana password
   - Configure proper CORS origins
   - Use secrets management for sensitive config
   - Disable docs endpoints in production (automatic)

2. **Scaling**:
   - Increase `WORKERS` environment variable
   - Use Redis cluster for high availability
   - Consider using Kubernetes for orchestration

3. **Alerting**:
   - Configure Alertmanager receivers (email, Slack, PagerDuty)
   - Review and customize alert rules

4. **Logging**:
   - Adjust Loki retention period as needed
   - Configure log levels appropriately

## License

MIT
