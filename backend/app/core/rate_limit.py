"""
Rate limiting implementation for API endpoints.
Uses an in-memory token bucket algorithm for simplicity and performance.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings
from app.core.exceptions import RateLimitError


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(self, rate: int, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per minute
            capacity: Maximum tokens in bucket (burst capacity)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if bucket is empty
        """
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.rate / 60.0)
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting requests."""

    def __init__(self, app, requests_per_minute: int = 60, burst: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(rate=requests_per_minute, capacity=burst)
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with rate limiting."""
        # Get client identifier (IP or authenticated user)
        client_id = self._get_client_id(request)

        # Check rate limit
        bucket = self.buckets[client_id]
        if not bucket.consume():
            raise RateLimitError(
                f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))

        return response

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Use authenticated user ID if available
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In production, decode JWT and use user ID
            return f"user:{auth_header[7:20]}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


def create_rate_limit_middleware() -> Tuple[type, Dict]:
    """Create rate limit middleware with settings."""
    settings = get_settings()
    return RateLimitMiddleware, {
        "requests_per_minute": settings.rate_limit_requests_per_minute,
        "burst": settings.rate_limit_burst,
    }
