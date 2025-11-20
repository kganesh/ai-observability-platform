#!/usr/bin/env python3
"""
Load test script to generate metrics for anomaly detection.
Generates HTTP requests to telemetry-demo-service to create:
- Normal traffic patterns
- Slow request patterns (for latency anomalies)
- Error patterns (for error rate anomalies)
"""

import requests
import time
import concurrent.futures
from typing import Dict, List
import argparse
import sys


class LoadTest:
    def __init__(self, base_url: str = "http://localhost:8080", max_workers: int = 10):
        self.base_url = base_url
        self.max_workers = max_workers
        self.results: Dict[str, List[Dict]] = {
            "normal": [],
            "slow": [],
            "error": []
        }
    
    def make_request(self, scenario: str, request_num: int) -> Dict:
        """Make a single HTTP request and return timing/status info."""
        url = f"{self.base_url}/checkout?scenario={scenario}"
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=30)
            elapsed = time.time() - start_time
            
            # For error scenario, 500 is expected
            is_success = response.status_code == 200 if scenario != "error" else response.status_code == 500
            
            result = {
                "scenario": scenario,
                "request_num": request_num,
                "status_code": response.status_code,
                "elapsed_time": elapsed,
                "success": is_success
            }
            
            return result
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            return {
                "scenario": scenario,
                "request_num": request_num,
                "status_code": None,
                "elapsed_time": elapsed,
                "success": False,
                "error": str(e)
            }
    
    def run_scenario(self, scenario: str, count: int, description: str):
        """Run requests for a specific scenario."""
        print(f"\n{'='*60}")
        print(f"Running {description}")
        print(f"Scenario: {scenario}, Count: {count}")
        print(f"{'='*60}")
        
        start_time = time.time()
        completed = 0
        failed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all requests
            futures = {
                executor.submit(self.make_request, scenario, i+1): i+1 
                for i in range(count)
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(futures):
                request_num = futures[future]
                try:
                    result = future.result()
                    self.results[scenario].append(result)
                    completed += 1
                    
                    if not result.get("success", False):
                        failed += 1
                    
                    # Progress indicator
                    if completed % 50 == 0 or completed == count:
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        print(f"  Progress: {completed}/{count} ({rate:.1f} req/s) - "
                              f"Failed: {failed}", end='\r')
                        
                except Exception as e:
                    print(f"\n  Error processing request {request_num}: {e}")
                    failed += 1
        
        total_time = time.time() - start_time
        print(f"\n  Completed: {completed}/{count} in {total_time:.2f}s "
              f"({completed/total_time:.1f} req/s)")
        print(f"  Failed: {failed}")
    
    def print_summary(self):
        """Print summary statistics."""
        print(f"\n{'='*60}")
        print("LOAD TEST SUMMARY")
        print(f"{'='*60}")
        
        for scenario in ["normal", "slow", "error"]:
            results = self.results[scenario]
            if not results:
                continue
            
            successful = [r for r in results if r.get("success", False)]
            failed = [r for r in results if not r.get("success", False)]
            
            if successful:
                elapsed_times = [r["elapsed_time"] for r in successful]
                avg_time = sum(elapsed_times) / len(elapsed_times)
                min_time = min(elapsed_times)
                max_time = max(elapsed_times)
                
                print(f"\n{scenario.upper()} Requests:")
                print(f"  Total: {len(results)}")
                print(f"  Successful: {len(successful)}")
                print(f"  Failed: {len(failed)}")
                print(f"  Avg Response Time: {avg_time*1000:.1f}ms")
                print(f"  Min Response Time: {min_time*1000:.1f}ms")
                print(f"  Max Response Time: {max_time*1000:.1f}ms")
            
            if failed:
                print(f"  Failed Requests: {len(failed)}")
                if len(failed) <= 5:
                    for f in failed:
                        error_msg = f.get("error", "Unknown error")
                        print(f"    - Request {f['request_num']}: {error_msg}")
    
    def run(self, normal_count: int = 200, slow_count: int = 200, error_count: int = 500):
        """Run the complete load test."""
        print(f"\n{'='*60}")
        print("LOAD TEST STARTING")
        print(f"{'='*60}")
        print(f"Target: {self.base_url}")
        print(f"Concurrency: {self.max_workers} workers")
        print(f"\nTest Plan:")
        print(f"  - {normal_count} normal requests")
        print(f"  - {slow_count} slow requests")
        print(f"  - {error_count} error requests")
        print(f"  Total: {normal_count + slow_count + error_count} requests")
        
        total_start = time.time()
        
        # Run scenarios
        if normal_count > 0:
            self.run_scenario("normal", normal_count, "Normal Requests")
            time.sleep(2)  # Small delay between scenarios
        
        if slow_count > 0:
            self.run_scenario("slow", slow_count, "Slow Requests (Latency Spikes)")
            time.sleep(2)
        
        if error_count > 0:
            self.run_scenario("error", error_count, "Error Requests")
        
        total_time = time.time() - total_start
        total_requests = normal_count + slow_count + error_count
        
        print(f"\n{'='*60}")
        print(f"LOAD TEST COMPLETED")
        print(f"{'='*60}")
        print(f"Total Requests: {total_requests}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Average Rate: {total_requests/total_time:.1f} req/s")
        
        self.print_summary()
        
        print(f"\n{'='*60}")
        print("NEXT STEPS")
        print(f"{'='*60}")
        print("1. Check Prometheus metrics: http://localhost:9090")
        print("2. Check anomaly-service logs for detected anomalies")
        print("3. Check incident-service for created incidents")
        print("4. View dashboard: http://localhost:5173")


def main():
    parser = argparse.ArgumentParser(
        description="Load test script for telemetry-demo-service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run default load test (200 normal, 200 slow, 500 error)
  python load_test.py
  
  # Run only normal requests
  python load_test.py --normal 100
  
  # Run with custom concurrency
  python load_test.py --workers 20
  
  # Run against different host
  python load_test.py --url http://localhost:8080
        """
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Base URL of telemetry-demo-service (default: http://localhost:8080)"
    )
    
    parser.add_argument(
        "--normal",
        type=int,
        default=200,
        help="Number of normal requests (default: 200)"
    )
    
    parser.add_argument(
        "--slow",
        type=int,
        default=200,
        help="Number of slow requests (default: 200)"
    )
    
    parser.add_argument(
        "--error",
        type=int,
        default=500,
        help="Number of error requests (default: 500)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Validate URL is reachable
    try:
        print(f"Checking connectivity to {args.url}...")
        response = requests.get(f"{args.url}/actuator/health", timeout=5)
        if response.status_code == 200:
            print("✓ Service is reachable")
        else:
            print(f"⚠ Service returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot reach service at {args.url}")
        print(f"  Error: {e}")
        print("\nMake sure telemetry-demo-service is running:")
        print("  docker compose up telemetry-demo-service")
        sys.exit(1)
    
    # Run load test
    load_test = LoadTest(base_url=args.url, max_workers=args.workers)
    load_test.run(
        normal_count=args.normal,
        slow_count=args.slow,
        error_count=args.error
    )


if __name__ == "__main__":
    main()

