"""
Load test configuration using Locust.
Simulates concurrent users sending triage requests.
"""

from locust import HttpUser, between, task


class TriageUser(HttpUser):
    """Simulated user for load testing the triage endpoint."""

    wait_time = between(1, 3)
    host = "http://localhost:8000"

    @task(3)
    def submit_triage_request(self):
        """Submit a triage request with common symptoms."""
        self.client.post(
            "/api/v1/triage",
            json={
                "patient_message": "مجھے سر درد اور بخار ہے",
                "location_lat": 33.6844,
                "location_lng": 73.0479,
            },
        )

    @task(1)
    def check_health(self):
        """Check health endpoint."""
        self.client.get("/api/v1/healthz")

    @task(1)
    def search_facilities(self):
        """Search for nearby facilities."""
        self.client.post(
            "/api/v1/facilities/search",
            json={
                "latitude": 33.6844,
                "longitude": 73.0479,
                "max_distance_km": 10.0,
            },
        )
