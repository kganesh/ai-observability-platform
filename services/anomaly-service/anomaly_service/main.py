import time
import requests
import psycopg2
import numpy as np

PROM_URL = "http://prometheus:9090/api/v1/query"
PG_CONN = psycopg2.connect(host="postgres", dbname="observability",
                          user="admin", password="admin")

def detect_anomaly(values):
    if len(values) < 5:
        return False
    mean = np.mean(values)
    std = np.std(values)
    if values[-1] > mean + 3 * std:
        return True
    return False

while True:
    r = requests.get(PROM_URL, params={'query': 'histogram_quantile(0.95, rate(http_server_request_duration_seconds_bucket[1m]))'})
    data = r.json()['data']['result'][0]['value'][1]
    value = float(data)

    # Simple sliding buffer
    if detect_anomaly([value]):
        cur = PG_CONN.cursor()
        cur.execute(
            "INSERT INTO anomalies (service_name, metric_name, severity, value) VALUES (%s, %s, %s, %s)",
            ("telemetry-demo-service", "p95_latency", "HIGH", value)
        )
        PG_CONN.commit()

    time.sleep(15)