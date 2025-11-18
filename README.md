# AI Observability Platform

An end-to-end, AI-driven observability platform designed to collect, analyze, and visualize telemetry data (metrics, traces, and logs) from microservices, detect anomalies, and perform AI-powered root cause analysis.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Service Endpoints](#service-endpoints)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Development Commands](#development-commands)
- [Monitoring & Visualization](#monitoring--visualization)
- [Common Metrics & Queries](#common-metrics--queries)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Spring Boot    │────▶│  OTEL Collector  │────▶│  Prometheus │
│   Services      │     │                  │     │  (Metrics)  │
└─────────────────┘     └──────────────────┘     └─────────────┘
                                │
                                │
                                ▼
                         ┌─────────────┐
                         │   Jaeger    │
                         │  (Traces)   │
                         └─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Grafana    │      │  Anomaly     │      │   LLM        │
│  (Dashboards)│      │  Service    │      │  Service     │
└──────────────┘      └──────────────┘      └──────────────┘
                              │                       │
                              └───────────┬───────────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │  PostgreSQL  │
                                   │ (Incidents)  │
                                   └──────────────┘
```

## Core Components

### Telemetry Collection
- **OpenTelemetry Collector**: Receives OTLP data (HTTP/gRPC) from services and routes traces to Jaeger and metrics to Prometheus.

### Backend Storage & Visualization
- **Prometheus**: Time-series database that scrapes metrics from the OTEL Collector.
- **Jaeger**: Distributed tracing backend for storing and querying trace data.
- **Grafana**: Unified dashboard platform with pre-configured data sources for Prometheus and Jaeger.
- **PostgreSQL**: Relational database storing anomaly detections and incident records.

### Application Services
- **`telemetry-demo-service`**: Spring Boot service (port 8080) that generates sample telemetry with normal/slow/error scenarios via `/checkout` endpoint.
- **`incident-service`**: Spring Boot service (port 8081) that manages incidents via REST API and stores them in PostgreSQL.

### AI/ML Services
- **`anomaly-service`**: Python service that queries Prometheus metrics to detect latency anomalies using statistical analysis (Z-score).
- **`llm-service`**: Python service (port 8000) using Google Gemini API for AI-powered root cause analysis of incidents.

### User Interface
- **`dashboard`**: React-based web dashboard (port 5173) for viewing incidents and anomalies.

## Service Endpoints

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| **Grafana** | http://localhost:3000 | 3000 | Metrics & traces dashboards (admin/admin) |
| **Prometheus** | http://localhost:9090 | 9090 | Metrics query UI |
| **Jaeger** | http://localhost:16686 | 16686 | Trace visualization UI |
| **Telemetry Demo** | http://localhost:8080 | 8080 | Sample service with `/checkout` endpoint |
| **Incident Service** | http://localhost:8081 | 8081 | REST API for incidents |
| **LLM Service** | http://localhost:8000 | 8000 | AI root cause analysis API |
| **Dashboard** | http://localhost:5173 | 5173 | React UI for incidents |
| **OTEL Collector** | http://localhost:8889/metrics | 8889 | Prometheus metrics endpoint |
| **PostgreSQL** | localhost:5432 | 5432 | Database (admin/admin) |

## Prerequisites

- **Docker** and **Docker Compose** (v2.0+)
- **Google Gemini API Key** (for LLM service)

## Getting Started

### 1. Configuration

Create a `.env` file in the project root directory:

```bash
# .env
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

### 2. Start All Services

```bash
cd infra
docker compose up -d
```

### 3. Verify Services

Check that all services are running:

```bash
docker compose ps
```

### 4. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
  - Pre-configured with Prometheus and Jaeger data sources
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686

## Development Commands

### Starting Services

```bash
# Start all services
docker compose up -d

# Start specific services
docker compose up -d postgres prometheus grafana jaeger otel-collector

# Start with rebuild
docker compose up --build -d

# Start specific services with rebuild
docker compose up --build telemetry-demo-service incident-service anomaly-service
```

### Stopping Services

```bash
# Stop all services
docker compose down

# Stop specific services
docker compose stop telemetry-demo-service

# Stop and remove volumes (clean slate)
docker compose down -v
```

### Building Services

```bash
# Rebuild all services
docker compose build

# Rebuild specific service
docker compose build anomaly-service

# Rebuild without cache
docker compose build --no-cache anomaly-service
```

### Viewing Logs

```bash
# Follow logs for all services
docker compose logs -f

# Follow logs for specific service
docker compose logs -f otel-collector
docker compose logs -f telemetry-demo-service
docker compose logs -f incident-service
docker compose logs -f anomaly-service
docker compose logs -f llm-service

# View last 100 lines
docker compose logs --tail=100 otel-collector

# View logs since timestamp
docker compose logs --since 10m otel-collector
```

### Restarting Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart telemetry-demo-service
docker compose restart otel-collector
```

### Container Management

```bash
# Execute command in running container
docker exec -it incident-service sh
docker exec -it telemetry-demo-service sh
docker exec -it anomaly-service bash

# View container resource usage
docker stats

# Inspect container configuration
docker inspect otel-collector

# Remove and recreate specific container
docker compose stop otel-collector
docker compose rm -f otel-collector
docker compose up -d otel-collector
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U admin -d observability

# Run SQL queries
docker exec -it postgres psql -U admin -d observability -c "SELECT * FROM incidents;"

# View database logs
docker compose logs -f postgres
```

## Monitoring & Visualization

### Grafana

Grafana is pre-configured with:
- **Prometheus** data source (default) - `http://prometheus:9090`
- **Jaeger** data source - `http://jaeger:16686`

**Access**: http://localhost:3000 (admin/admin)

**Features**:
- Create custom dashboards for metrics
- Explore traces from Jaeger
- Correlate metrics and traces
- Set up alerts

### Prometheus

**Access**: http://localhost:9090

**Useful Queries**:
- View all metrics: `{__name__=~".+"}`
- Service-specific metrics: `{service_name="telemetry-demo-service"}`
- HTTP request rate: `rate(http_server_requests_seconds_count[5m])`

### Jaeger

**Access**: http://localhost:16686

**Features**:
- Search traces by service, operation, or tags
- View trace timeline and spans
- Analyze service dependencies

### Testing Telemetry Generation

```bash
# Generate normal request
curl http://localhost:8080/checkout

# Generate slow request (adds delay)
curl http://localhost:8080/checkout?delay=2000

# Generate error request
curl http://localhost:8080/checkout?error=true

# Check OTEL Collector metrics endpoint
curl http://localhost:8889/metrics
```

## Common Metrics & Queries

### Prometheus Metrics

The platform collects the following metrics:

**HTTP Metrics**:
- `http_server_requests_seconds_count` - Total request count
- `http_server_requests_seconds_sum` - Total request duration
- `http_server_requests_seconds_bucket` - Request duration histogram

**JVM Metrics**:
- `jvm_memory_used_bytes` - Memory usage
- `jvm_threads_live` - Active threads
- `jvm_gc_pause_seconds` - GC pause duration

**Custom Metrics**:
- Service-specific metrics with `service.name` label

### Example Prometheus Queries

```promql
# Request rate per service
rate(http_server_requests_seconds_count[5m])

# Average request duration
rate(http_server_requests_seconds_sum[5m]) / rate(http_server_requests_seconds_count[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_server_requests_seconds_bucket[5m]))

# Error rate
rate(http_server_requests_seconds_count{status=~"5.."}[5m])

# Memory usage by service
jvm_memory_used_bytes{service_name="telemetry-demo-service"}
```

## Troubleshooting

### Service Not Starting

```bash
# Check service status
docker compose ps

# Check service logs
docker compose logs <service-name>

# Verify network connectivity
docker network inspect infra_observability-net
```

### OTEL Collector Issues

```bash
# Check collector logs
docker compose logs -f otel-collector

# Verify collector configuration
docker exec -it otel-collector cat /etc/otel-collector-config.yml

# Test collector metrics endpoint
curl http://localhost:8889/metrics

# Restart collector
docker compose restart otel-collector
```

### Prometheus Not Scraping

```bash
# Check Prometheus targets
# Visit: http://localhost:9090/targets

# Verify Prometheus config
docker exec -it prometheus cat /etc/prometheus/prometheus.yml

# Check Prometheus logs
docker compose logs -f prometheus
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker compose ps postgres

# Test connection
docker exec -it postgres psql -U admin -d observability -c "SELECT 1;"

# Check database logs
docker compose logs -f postgres
```

### Service Communication Issues

```bash
# Test connectivity from container
docker exec -it incident-service sh
# Inside container:
apk add curl  # if curl is missing
curl -v http://otel-collector:4318/v1/traces
curl -v http://prometheus:9090/api/v1/query?query=up
```

### Grafana Data Source Issues

```bash
# Check Grafana logs
docker compose logs -f grafana

# Verify provisioning config
docker exec -it grafana cat /etc/grafana/provisioning/datasources/datasources.yml

# Restart Grafana
docker compose restart grafana
```

### Rebuild Everything

```bash
# Complete clean rebuild
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Check Service Health

```bash
# Test telemetry demo service
curl http://localhost:8080/checkout

# Test incident service
curl http://localhost:8081/api/incidents

# Test LLM service
curl http://localhost:8000/health

# Check anomaly service logs
docker compose logs -f anomaly-service
```

## Additional Resources

- **OpenTelemetry**: https://opentelemetry.io/
- **Prometheus**: https://prometheus.io/docs/
- **Jaeger**: https://www.jaegertracing.io/docs/
- **Grafana**: https://grafana.com/docs/
- **Google Gemini API**: https://ai.google.dev/
- **PostgreSQL**: https://www.postgresql.org/docs/current/
- **Docker**: https://docs.docker.com/