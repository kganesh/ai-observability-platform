CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    service_name TEXT,
    status TEXT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    rca_text TEXT
);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    incident_id INT,
    service_name TEXT,
    metric_name TEXT,
    severity TEXT,
    value DOUBLE PRECISION,
    baseline DOUBLE PRECISION,
    timestamp TIMESTAMP
);