# AI Observability Platform

This project provides an end-to-end, AI-driven observability platform. It is designed to collect, analyze, and visualize telemetry data (metrics, traces, and logs) from microservices, detect anomalies, and perform AI-powered root cause analysis.

## Core Components

*   **Telemetry Collection:** OpenTelemetry Collector receives data from services.
*   **Backend Storage & Visualization:**
    *   **Prometheus:** Stores metrics scraped from the OTEL Collector.
    *   **Jaeger:** Stores and visualizes distributed traces.
    *   **Grafana:** Provides dashboards for visualizing metrics (not pre-configured).
    *   **PostgreSQL:** Stores anomaly and incident data.
*   **Application Services:**
    *   `telemetry-demo-service`: A Spring Boot service to generate sample telemetry.
    *   `incident-service`: A Spring Boot service to manage incidents.
*   **AI/ML Services:**
    *   `anomaly-service`: A Python service that queries Prometheus to detect latency anomalies.
    *   `llm-service`: A Python service using a Large Language Model (LLM) for root cause analysis.
*   **User Interface:**
    *   `dashboard`: A React-based dashboard to view incidents.

## Prerequisites

*   Docker and Docker Compose
*   A Google Gemini API Key

## Getting Started

### 1. Configuration

The `llm-service` requires a Google Gemini API key. The `docker-compose.yml` file is configured to read this key from a `.env` file at the root of the project.

Create a file named `.env` in the project's root directory and add your API key:

```bash
# .env
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

Few docker commands for troubleshooting

```bash

docker exec -it incident-service sh
# inside:
apk add curl  # only if curl is missing
curl -v http://otel-collector:4318/v1/traces

```

```bash
docker compose up --build telemetry-demo-service incident-service anomaly-service
```

```bash
docker compose down
docker compose stop otel-collector
docker compose rm -f otel-collector
docker compose up -d otel-collector
docker compose logs -f otel-collector
docker compose restart telemetry-demo-service
docker compose logs -f telemetry-demo-service
docker compose build anomaly-service
docker compose up -d anomaly-service
docker compose logs -f anomaly-service   # verify it connects to Postgres

curl http://localhost:8889/metrics
```
Prometheus metrics
http_server_requests_seconds_count
http_server_requests_seconds_sum
http_server_requests_seconds_bucket (histogram)
JVM metrics (memory, threads, etc.)