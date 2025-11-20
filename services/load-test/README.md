# Load Test Script

This script generates HTTP traffic to the telemetry-demo-service to create metrics for anomaly detection.

## Usage

### Basic Usage

Run the default load test (200 normal, 200 slow, 500 error requests):

```bash
python load_test.py
```

### Custom Configuration

```bash
# Run only normal requests
python load_test.py --normal 100

# Run with more concurrent workers
python load_test.py --workers 20

# Run against different host
python load_test.py --url http://localhost:8080

# Custom request counts
python load_test.py --normal 100 --slow 50 --error 200
```

### Command Line Options

- `--url`: Base URL of telemetry-demo-service (default: http://localhost:8080)
- `--normal`: Number of normal requests (default: 200)
- `--slow`: Number of slow requests (default: 200)
- `--error`: Number of error requests (default: 500)
- `--workers`: Number of concurrent workers (default: 10)

## What It Does

1. **Normal Requests**: Generates baseline traffic patterns
2. **Slow Requests**: Creates latency spikes that should trigger anomaly detection
3. **Error Requests**: Generates error patterns for error rate monitoring

## Expected Results

After running the load test:

1. **Prometheus** should show metrics at http://localhost:9090
2. **Anomaly Service** should detect anomalies from the slow requests
3. **Incident Service** should create incidents based on detected anomalies
4. **Dashboard** should display the incidents at http://localhost:5173

## Installation

```bash
pip install -r requirements.txt
```

## Troubleshooting

If the service is not reachable:
- Make sure telemetry-demo-service is running: `docker compose up telemetry-demo-service`
- Check the service is accessible: `curl http://localhost:8080/actuator/health`

