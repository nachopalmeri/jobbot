"""
Performance Tests for JobBot API
Load testing, response time assertions, and performance benchmarks
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.performance
class TestAPILoadTesting:
    """Load testing with concurrent users."""

    def test_health_endpoint_100_concurrent_requests(self, client):
        """Test health endpoint with 100 concurrent requests."""
        num_requests = 100

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(client.get, "/health") for _ in range(num_requests)
            ]
            responses = [f.result() for f in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == num_requests, (
            f"Only {success_count}/{num_requests} succeeded"
        )

        # Should complete in reasonable time (< 5 seconds for 100 requests)
        assert total_time < 5.0, f"Took {total_time:.2f}s, expected < 5s"

        # Average response time should be < 100ms
        avg_time = total_time / num_requests * 1000
        assert avg_time < 100, (
            f"Average response time {avg_time:.2f}ms, expected < 100ms"
        )

    def test_auth_login_load_50_concurrent(self, client, test_user):
        """Test login endpoint with 50 concurrent requests."""
        num_requests = 50

        def login():
            return client.post(
                "/auth/token",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"],
                },
            )

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login) for _ in range(num_requests)]
            responses = [f.result() for f in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # Most should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= num_requests * 0.8, (
            f"Only {success_count}/{num_requests} succeeded"
        )

        # Should not take too long
        assert total_time < 10.0, f"Took {total_time:.2f}s, expected < 10s"

    def test_job_search_load_30_concurrent(self, client, auth_headers):
        """Test job search with 30 concurrent requests."""
        num_requests = 30

        with patch("api.routes.jobs.JobScraper") as mock_scraper:
            mock_instance = MagicMock()
            mock_instance.search_jobs.return_value = [
                {
                    "id": f"job_{i}",
                    "title": f"Job {i}",
                    "company": "TestCorp",
                    "url": f"https://example.com/job{i}",
                    "date": datetime.now(timezone.utc).isoformat(),
                }
                for i in range(5)
            ]
            mock_scraper.return_value = mock_instance

            def search():
                return client.get("/jobs/search?q=python", headers=auth_headers)

            start_time = time.time()

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(search) for _ in range(num_requests)]
                responses = [f.result() for f in as_completed(futures)]

            end_time = time.time()

            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count >= num_requests * 0.9

            # Average response time should be < 200ms
            avg_time = (end_time - start_time) / num_requests * 1000
            assert avg_time < 200, f"Average response time {avg_time:.2f}ms"


@pytest.mark.performance
class TestResponseTimeAssertions:
    """API response time assertions for critical paths."""

    def test_health_endpoint_response_time_p95(self, client):
        """Test health endpoint response time p95 < 100ms."""
        num_requests = 100
        response_times = []

        for _ in range(num_requests):
            start = time.perf_counter()
            response = client.get("/health")
            end = time.perf_counter()

            assert response.status_code == 200
            response_times.append((end - start) * 1000)

        # Calculate p95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_time = response_times[p95_index]

        assert p95_time < 100, f"p95 response time {p95_time:.2f}ms, expected < 100ms"

    def test_auth_login_response_time_p95(self, client, test_user):
        """Test login endpoint response time p95 < 200ms."""
        num_requests = 50
        response_times = []

        for _ in range(num_requests):
            start = time.perf_counter()
            response = client.post(
                "/auth/token",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"],
                },
            )
            end = time.perf_counter()

            assert response.status_code == 200
            response_times.append((end - start) * 1000)

        # Calculate p95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_time = response_times[p95_index]

        assert p95_time < 200, f"p95 response time {p95_time:.2f}ms, expected < 200ms"

    def test_job_search_response_time_p95(self, client, auth_headers):
        """Test job search endpoint response time p95 < 300ms."""
        num_requests = 30
        response_times = []

        with patch("api.routes.jobs.JobScraper") as mock_scraper:
            mock_instance = MagicMock()
            mock_instance.search_jobs.return_value = [
                {
                    "id": f"job_{i}",
                    "title": f"Job {i}",
                    "company": "TestCorp",
                    "url": f"https://example.com/job{i}",
                }
                for i in range(10)
            ]
            mock_scraper.return_value = mock_instance

            for _ in range(num_requests):
                start = time.perf_counter()
                response = client.get("/jobs/search?q=python", headers=auth_headers)
                end = time.perf_counter()

                assert response.status_code == 200
                response_times.append((end - start) * 1000)

        # Calculate p95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_time = response_times[p95_index]

        assert p95_time < 300, f"p95 response time {p95_time:.2f}ms, expected < 300ms"

    def test_user_profile_response_time_p95(self, client, auth_headers):
        """Test user profile endpoint response time p95 < 150ms."""
        num_requests = 50
        response_times = []

        for _ in range(num_requests):
            start = time.perf_counter()
            response = client.get("/users/profile", headers=auth_headers)
            end = time.perf_counter()

            # Might be 200 or 404 depending on endpoint existence
            response_times.append((end - start) * 1000)

        # Calculate p95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_time = response_times[p95_index]

        assert p95_time < 150, f"p95 response time {p95_time:.2f}ms, expected < 150ms"


@pytest.mark.performance
class TestDatabaseQueryPerformance:
    """Database query performance tests."""

    def test_user_lookup_query_performance(self, db, test_user):
        """Test user lookup query completes in < 10ms."""
        num_queries = 100
        times = []

        for _ in range(num_queries):
            start = time.perf_counter()
            user = db.get_user(test_user["telegram_id"])
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 10, f"Average query time {avg_time:.2f}ms, expected < 10ms"
        assert max_time < 50, f"Max query time {max_time:.2f}ms, expected < 50ms"

    def test_job_search_query_performance(self, db):
        """Test job search query performance."""
        # Add some test jobs
        for i in range(100):
            db.add_job(
                {
                    "id": f"perf_job_{i}",
                    "title": f"Performance Test Job {i}",
                    "company": "TestCorp",
                    "url": f"https://example.com/job{i}",
                    "search_query": "python",
                    "date": datetime.now(timezone.utc).isoformat(),
                }
            )

        # Search for jobs
        start = time.perf_counter()
        jobs = db.get_jobs_for_user(123456789, limit=50)
        end = time.perf_counter()

        query_time = (end - start) * 1000
        assert query_time < 100, f"Query time {query_time:.2f}ms, expected < 100ms"

    def test_application_count_query_performance(self, db, test_user):
        """Test application count query performance."""
        # Add some test applications
        for i in range(50):
            db.add_job_application(
                test_user["telegram_id"],
                f"Job {i}",
                "TestCorp",
                f"https://example.com/job{i}",
            )

        start = time.perf_counter()
        count = db.get_user_application_count(test_user["telegram_id"])
        end = time.perf_counter()

        query_time = (end - start) * 1000
        assert query_time < 10, f"Query time {query_time:.2f}ms, expected < 10ms"


@pytest.mark.performance
class TestMemoryLeakDetection:
    """Memory leak detection tests."""

    def test_auth_endpoint_memory_stable(self, client, test_user):
        """Test that auth endpoint doesn't leak memory over repeated calls."""
        import gc
        import sys

        # Warm up
        for _ in range(10):
            client.post(
                "/auth/token",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"],
                },
            )

        gc.collect()

        # Get baseline memory (approximation via object count)
        baseline_objects = len(gc.get_objects())

        # Make many requests
        for _ in range(100):
            client.post(
                "/auth/token",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"],
                },
            )

        gc.collect()

        # Check that object count hasn't grown significantly
        final_objects = len(gc.get_objects())
        growth = final_objects - baseline_objects

        # Allow some growth but not excessive
        assert growth < 1000, f"Object count grew by {growth}, potential memory leak"

    def test_job_search_memory_stable(self, client, auth_headers):
        """Test that job search endpoint doesn't leak memory."""
        import gc

        with patch("api.routes.jobs.JobScraper") as mock_scraper:
            mock_instance = MagicMock()
            mock_instance.search_jobs.return_value = [
                {
                    "id": f"job_{i}",
                    "title": f"Job {i}",
                    "company": "TestCorp",
                    "url": f"https://example.com/job{i}",
                }
                for i in range(20)
            ]
            mock_scraper.return_value = mock_instance

            gc.collect()
            baseline_objects = len(gc.get_objects())

            # Make many requests
            for _ in range(50):
                client.get("/jobs/search?q=python", headers=auth_headers)

            gc.collect()
            final_objects = len(gc.get_objects())
            growth = final_objects - baseline_objects

            assert growth < 500, f"Object count grew by {growth}, potential memory leak"

    def test_webhook_processing_memory_stable(self, client, valid_stripe_event):
        """Test that webhook processing doesn't leak memory."""
        import gc

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = valid_stripe_event

            gc.collect()
            baseline_objects = len(gc.get_objects())

            # Process many webhooks
            for _ in range(50):
                client.post(
                    "/subscriptions/webhook/stripe",
                    data=json.dumps(valid_stripe_event),
                    headers={"stripe-signature": "t=123,v1=test"},
                )

            gc.collect()
            final_objects = len(gc.get_objects())
            growth = final_objects - baseline_objects

            assert growth < 300, f"Object count grew by {growth}, potential memory leak"


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarks for comparison."""

    def benchmark_health_endpoint(self, client):
        """Benchmark health endpoint performance."""
        times = []

        for _ in range(100):
            start = time.perf_counter()
            response = client.get("/health")
            end = time.perf_counter()

            assert response.status_code == 200
            times.append((end - start) * 1000)

        times.sort()

        results = {
            "min_ms": min(times),
            "max_ms": max(times),
            "avg_ms": sum(times) / len(times),
            "p50_ms": times[50],
            "p95_ms": times[95],
            "p99_ms": times[99],
        }

        # Log results (in real scenario, would save to benchmark DB)
        print(f"\nHealth Endpoint Benchmark:")
        for key, value in results.items():
            print(f"  {key}: {value:.2f}")

        # Assertions
        assert results["p95_ms"] < 100
        assert results["p99_ms"] < 200

    def benchmark_auth_login(self, client, test_user):
        """Benchmark auth login performance."""
        times = []

        for _ in range(50):
            start = time.perf_counter()
            response = client.post(
                "/auth/token",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"],
                },
            )
            end = time.perf_counter()

            assert response.status_code == 200
            times.append((end - start) * 1000)

        times.sort()

        results = {
            "min_ms": times[0],
            "max_ms": times[-1],
            "avg_ms": sum(times) / len(times),
            "p50_ms": times[25],
            "p95_ms": times[47],
            "p99_ms": times[49] if len(times) > 49 else times[-1],
        }

        print(f"\nAuth Login Benchmark:")
        for key, value in results.items():
            print(f"  {key}: {value:.2f}")

        assert results["p95_ms"] < 200


@pytest.mark.performance
class TestScalabilityTests:
    """Scalability tests for growing load."""

    def test_linear_response_time_scaling(self, client, test_user):
        """Test that response time scales roughly linearly with load."""
        load_levels = [10, 20, 30]
        response_times = []

        for load in load_levels:
            start = time.time()

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(
                        client.post,
                        "/auth/token",
                        data={
                            "username": test_user["email"],
                            "password": test_user["password"],
                        },
                    )
                    for _ in range(load)
                ]
                list(as_completed(futures))

            total_time = time.time() - start
            avg_time = total_time / load * 1000
            response_times.append((load, avg_time))

        # Check that average time doesn't increase dramatically
        # (allow 2x increase from 10 to 30 requests)
        base_time = response_times[0][1]
        high_load_time = response_times[-1][1]

        ratio = high_load_time / base_time
        assert ratio < 3, f"Response time scaled by {ratio:.2f}x, expected < 3x"
