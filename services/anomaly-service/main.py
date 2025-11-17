import os
import time
import requests
import psycopg2
import psycopg2.extras
import numpy as np

PROM_URL = os.getenv("PROM_URL", "http://prometheus:9090/api/v1/query")
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_DB = os.getenv("PG_DB", "observability")
PG_USER = os.getenv("PG_USER", "admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "admin")

OTEL_RESOURCE_ATTRIBUTES=service.name=anomaly-service

QUERY = 'histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[1m])) by (le))'
WINDOW_SIZE = 10
latency_window: list[float] = []


def log(msg: str):
    print(f"[anomaly-service] {msg}", flush=True)


def get_pg_conn():
    """Retryable Postgres connection."""
    while True:
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                dbname=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD,
            )
            conn.autocommit = True
            log("Connected to Postgres")
            return conn
        except Exception as e:
            log(f"Postgres not ready or unreachable at {PG_HOST}: {e}. Retrying in 3s...")
            time.sleep(3)


def fetch_p95_latency() -> float | None:
    """Query Prometheus for p95 latency. Returns None if no data yet."""
    try:
        resp = requests.get(PROM_URL, params={"query": QUERY}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("data", {}).get("result", [])
        if not result:
            log("No latency data from Prometheus yet.")
            return None

        value = float(result[0]["value"][1])
        return value
    except Exception as e:
        log(f"Error querying Prometheus: {e}")
        return None


def detect_anomaly(window: list[float]) -> bool:
    """Very simple z-score anomaly detection."""
    if len(window) < 5:
        return False
    arr = np.array(window)
    mean = arr.mean()
    std = arr.std() or 1.0
    z = (arr[-1] - mean) / std
    log(f"Latest p95={arr[-1]:.3f}, mean={mean:.3f}, std={std:.3f}, z={z:.2f}")
    return z > 3.0


def main():
    conn = get_pg_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    while True:
        value = fetch_p95_latency()
        if value is not None:
            latency_window.append(value)
            if len(latency_window) > WINDOW_SIZE:
                latency_window.pop(0)

            if detect_anomaly(latency_window):
                log("Anomaly detected! Inserting into DB.")
                baseline = float(np.mean(latency_window[:-1])) if len(latency_window) > 1 else value
                try:
                    cur.execute(
                        """
                        INSERT INTO anomalies (service_name, metric_name, severity, value, baseline, timestamp)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            "telemetry-demo-service",
                            "p95_latency",
                            "HIGH",
                            value,
                            baseline,
                        ),
                    )
                except Exception as e:
                    log(f"Failed to insert anomaly: {e}")

        time.sleep(15)


if __name__ == "__main__":
    main()
