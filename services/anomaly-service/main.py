import os
import time
import requests
import psycopg2
import psycopg2.extras
import numpy as np

# Prometheus URL - uses service name for Docker, or localhost for host testing
# Inside Docker: http://prometheus:9090 (service name)
# From host: http://localhost:9090
# To test manually: curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, sum(rate(http_server_requests_milliseconds_bucket[1m])) by (le))"
PROM_URL = os.getenv("PROM_URL", "http://prometheus:9090/api/v1/query")
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_DB = os.getenv("PG_DB", "observability")
PG_USER = os.getenv("PG_USER", "admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "admin")

OTEL_RESOURCE_ATTRIBUTES="service.name=anomaly-service"

# Prometheus query for p95 latency
# Note: Metric name may vary based on OpenTelemetry Collector transformation
# Common variants:
# - http_server_requests_milliseconds_bucket (Micrometer with milliseconds)
# - http_server_requests_seconds_bucket (Micrometer with seconds)
# - http_server_request_duration_seconds_bucket (OpenTelemetry semantic)
# Make query configurable via environment variable
# If using milliseconds, result will be in ms - we convert to seconds in fetch_p95_latency()
# Using 5m window for more stable results (histogram_quantile needs sufficient data)
DEFAULT_QUERY = 'histogram_quantile(0.95, sum(rate(http_server_requests_milliseconds_bucket[5m])) by (le))'
QUERY = os.getenv("PROMETHEUS_QUERY", DEFAULT_QUERY)
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


def check_metric_has_data(metric_name: str) -> bool:
    """Check if a metric exists and has data points."""
    try:
        base_url = PROM_URL.replace("/api/v1/query", "")
        # Query for the metric count to see if it has data
        query = f"count({metric_name})"
        resp = requests.get(PROM_URL, params={"query": query}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                result = data.get("data", {}).get("result", [])
                if result and len(result) > 0:
                    count = float(result[0]["value"][1])
                    return count > 0
        return False
    except Exception:
        return False


def check_metric_has_le_label(metric_name: str) -> bool:
    """Check if a histogram metric has the 'le' label required for quantiles."""
    try:
        base_url = PROM_URL.replace("/api/v1/query", "")
        series_url = f"{base_url}/api/v1/series"
        
        # Check for the metric with an 'le' label
        resp = requests.get(series_url, params={"match[]": f'{metric_name}{{le!=""}}'}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data") and len(data["data"]) > 0:
                log(f"✓ Metric '{metric_name}' has the 'le' label.")
                return True
        
        log(f"✗ Metric '{metric_name}' is missing the 'le' label.")
        log("  This is required for histogram_quantile. Check collector/prometheus config for label stripping.")
        return False
    except Exception as e:
        log(f"Error checking for 'le' label on {metric_name}: {e}")
        return False


def discover_metrics() -> list[str]:
    """Discover available HTTP request metrics in Prometheus."""
    metric_patterns = [
        "http_server_requests_milliseconds_bucket",
        "http_server_requests_seconds_bucket",
        "http_server_request_duration_seconds_bucket",
        "http_server_request_duration_milliseconds_bucket",
    ]
    
    found_metrics = []
    base_url = PROM_URL.replace("/api/v1/query", "")
    
    for pattern in metric_patterns:
        try:
            # Use Prometheus series API to check if metric exists
            series_url = f"{base_url}/api/v1/series"
            resp = requests.get(series_url, params={"match[]": f"{pattern}"}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data"):
                    # Also check if it has actual data points
                    has_data = check_metric_has_data(pattern)
                    if has_data:
                        check_metric_has_le_label(pattern)  # Add check for 'le' label
                        found_metrics.append(pattern)
                        log(f"Found metric with data: {pattern}")
                    else:
                        log(f"Found metric but no data yet: {pattern}")
        except Exception as e:
            log(f"Error checking metric {pattern}: {e}")
    
    return found_metrics


def try_alternative_queries() -> float | None:
    """Try multiple query variations to find one that works."""
    queries_to_try = [
        # Milliseconds variants
        'histogram_quantile(0.95, sum(rate(http_server_requests_milliseconds_bucket[1m])) by (le))',
        'histogram_quantile(0.95, sum(rate(http_server_requests_milliseconds_bucket[5m])) by (le))',
        
        # With service name filter
        'histogram_quantile(0.95, sum(rate(http_server_requests_milliseconds_bucket{service_name="telemetry-demo-service"}[1m])) by (le))',
        'histogram_quantile(0.95, sum(rate(http_server_requests_milliseconds_bucket{service_name="telemetry-demo-service"}[5m])) by (le))'
    ]
    
    for query in queries_to_try:
        try:
            resp = requests.get(PROM_URL, params={"query": query}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status") == "error":
                continue
            
            result = data.get("data", {}).get("result", [])
            if result:
                value_str = result[0]["value"][1]
                value = float(value_str)
                
                # Skip NaN or invalid values
                if value_str in ["NaN", "nan", "+Inf", "-Inf"] or (isinstance(value, float) and value != value):
                    continue
                
                # Convert milliseconds to seconds if needed
                if "milliseconds" in query.lower():
                    value = value / 1000.0
                
                log(f"Successfully found data with query: {query}")
                log(f"Result: {value:.3f}s")
                return value
        except Exception:
            continue
    
    return None


def fetch_p95_latency() -> float | None:
    """Query Prometheus for p95 latency. Returns None if no data yet."""
    try:
        resp = requests.get(PROM_URL, params={"query": QUERY}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        # Check for Prometheus query errors
        if data.get("status") == "error":
            error_msg = data.get("error", "Unknown error")
            log(f"Prometheus query error: {error_msg}")
            log(f"Query used: {QUERY}")
            log("Attempting to discover available metrics and try alternative queries...")
            
            # Try to discover metrics
            found = discover_metrics()
            if found:
                log(f"Found {len(found)} matching metrics: {found}")
            else:
                log("No HTTP request metrics found. Make sure:")
                log("  1. Telemetry-demo-service is running and receiving requests")
                log("  2. Metrics are being exported to OpenTelemetry Collector")
                log("  3. Prometheus is scraping the collector")
                log("  4. Try: curl http://localhost:8080/checkout to generate metrics")
            
            # Try alternative queries
            return try_alternative_queries()
        
        result = data.get("data", {}).get("result", [])
        if not result:
            log(f"No latency data from Prometheus. Query: {QUERY}")
            log("Attempting alternative queries...")
            
            # Try alternative queries
            alt_result = try_alternative_queries()
            if alt_result is not None:
                return alt_result
            
            log("No data found with any query variant. Possible issues:")
            log("  1. No requests have been made to telemetry-demo-service yet")
            log("  2. Metric name doesn't match (check Prometheus UI at http://localhost:9090)")
            log("  3. Time range issue - try increasing [1m] to [5m] or [10m]")
            log("  4. Check Prometheus targets: http://localhost:9090/targets")
            return None
        
        # Log the raw result for debugging
        if len(result) > 0:
            log(f"Raw Prometheus result: {result[0]}")

        # Extract value from Prometheus response
        # Prometheus returns: [timestamp, "value_as_string"]
        value_str = result[0]["value"][1]
        value = float(value_str)
        
        # Check for NaN or invalid values
        if value_str in ["NaN", "nan", "+Inf", "-Inf", "+Infinity", "-Infinity"] or (isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf'))):
            log(f"Prometheus returned invalid value: {value_str}")
            log(f"Full result: {result[0]}")
            log("This usually means:")
            log("  1. No data in the time range - try increasing [1m] to [5m]")
            log("  2. Metric doesn't exist or has no samples")
            log("  3. Query is incorrect")
            return None
        
        # Convert milliseconds to seconds if metric is in milliseconds
        # Check if query uses milliseconds bucket
        if "milliseconds" in QUERY.lower():
            original_ms = value
            value = value / 1000.0  # Convert ms to seconds
            log(f"Converted latency from {original_ms:.1f}ms to {value:.3f}s")
        
        return value
    except Exception as e:
        log(f"Error querying Prometheus: {e}")
        log(f"Query used: {QUERY}")
        log("Attempting alternative queries...")
        return try_alternative_queries()


def detect_anomaly(window: list[float], threshold: float = 3.0) -> bool:
    """Very simple z-score anomaly detection."""
    if len(window) < 3:
        return False
    arr = np.array(window)
    mean = arr.mean()
    std = arr.std() or 1.0
    z = (arr[-1] - mean) / std
    log(f"Latest p95={arr[-1]:.3f}, mean={mean:.3f}, std={std:.3f}, z={z:.2f}, threshold={threshold:.2f}")
    return z > threshold


# Modify main() function around line 77-102
def main():
    conn = get_pg_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Make threshold configurable
    ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "2.5"))  # Lower default
    MIN_WINDOW_SIZE = int(os.getenv("MIN_WINDOW_SIZE", "3"))  # Lower from 5 to 3

    # Initial diagnostic check
    log("=" * 60)
    log("Anomaly Service Starting - Diagnostic Check")
    log("=" * 60)
    log(f"Prometheus URL: {PROM_URL}")
    log(f"Query: {QUERY}")
    
    # Check Prometheus connectivity
    try:
        health_url = PROM_URL.replace("/api/v1/query", "/-/healthy")
        resp = requests.get(health_url, timeout=5)
        if resp.status_code == 200:
            log("✓ Prometheus is reachable")
        else:
            log(f"⚠ Prometheus health check returned: {resp.status_code}")
    except Exception as e:
        log(f"✗ Cannot reach Prometheus: {e}")
        log("  Make sure Prometheus is running and accessible")
    
    # Discover available metrics
    log("Discovering available HTTP request metrics...")
    found_metrics = discover_metrics()
    if found_metrics:
        log(f"✓ Found {len(found_metrics)} metric(s): {', '.join(found_metrics)}")
    else:
        log("✗ No HTTP request metrics found")
        log("  This is normal if no requests have been made yet.")
        log("  Try: curl http://localhost:8080/checkout")
    
    log("=" * 60)
    log("Starting anomaly detection loop...")
    log("=" * 60)

    while True:
        value = fetch_p95_latency()
        if value is not None:
            # Additional validation - skip NaN values
            import math
            if math.isnan(value) or math.isinf(value):
                log(f"Skipping invalid latency value: {value}")
            else:
                latency_window.append(value)
                log(f"Collected latency: {value:.3f}s (window size: {len(latency_window)})")
                if len(latency_window) > WINDOW_SIZE:
                    latency_window.pop(0)

            if len(latency_window) >= MIN_WINDOW_SIZE:
                if detect_anomaly(latency_window, ANOMALY_THRESHOLD):
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
                        log(f"Successfully inserted anomaly: value={value:.3f}, baseline={baseline:.3f}")
                    except Exception as e:
                        log(f"Failed to insert anomaly: {e}")
            else:
                log(f"Building window: {len(latency_window)}/{MIN_WINDOW_SIZE} samples")
        else:
            log("No latency data available from Prometheus")

        time.sleep(15)


if __name__ == "__main__":
    main()
