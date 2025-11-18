# AI Observability Platform

This is an end-to-end AI-driven observability platform built on:

- OpenTelemetry (metrics, logs, traces)
- Prometheus, Loki, Jaeger, Grafana
- AI anomaly detection (Python)
- LLM-based Root Cause Analysis (Python + LLM API)
- Java Spring Boot microservices (incident aggregation)
- React dashboard for visualizing incidents

## How to Run Everything

## LLM Service

The `llm-service` provides root cause analysis for incidents using Google's Gemini Pro model.

### Setup

1.  Navigate to the `services/llm-service` directory.
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set the `GEMINI_API_KEY` environment variable with your API key:
    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY"
    ```

### Running the Service

To start the service, run the following command from the `services/llm-service` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
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