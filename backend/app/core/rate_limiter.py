import hashlib
import time
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from backend.app.core.redis import get_redis_client


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter backed by Redis with in-memory fallback.
    Prevents brute-force, scraping, spam, and DoS attacks.
    """

    # In-memory storage fallback: key -> list of timestamps
    _memory_store: Dict[str, list] = {}

    def __init__(self, requests: int = 60, window_seconds: int = 60, key_prefix: str = "rl"):
        self.max_requests = requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def _get_client_identifier(self, request: Request) -> str:
        """Derive anonymous salted client identifier from IP or Auth header."""
        auth_header = request.headers.get("Authorization")
        if auth_header and "Bearer" in auth_header:
            token = auth_header.split("Bearer")[-1].strip()
            return hashlib.sha256(token.encode()).hexdigest()[:16]

        client_ip = request.client.host if request.client else "127.0.0.1"
        return hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    async def __call__(self, request: Request):
        client_id = self._get_client_identifier(request)
        path_key = request.url.path.replace("/", "_")
        key = f"{self.key_prefix}:{path_key}:{client_id}"
        now = time.time()

        # 1. Try Redis sliding window with sorted set
        try:
            redis = await get_redis_client()
            if redis:
                pipe = redis.pipeline()
                window_start = now - self.window_seconds

                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                # Count current window entries
                pipe.zcard(key)
                # Add current entry
                pipe.zadd(key, {str(now): now})
                # Expire key
                pipe.expire(key, self.window_seconds + 5)
                results = await pipe.execute()

                current_count = results[1]
                if current_count >= self.max_requests:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds.",
                        headers={"Retry-After": str(self.window_seconds)},
                    )
                return True
        except HTTPException:
            raise
        except Exception:
            # Fall through to in-memory fallback if Redis is unavailable or in unit tests
            pass

        # 2. In-memory sliding window fallback
        timestamps = self._memory_store.get(key, [])
        window_start = now - self.window_seconds
        # Clean expired
        valid_timestamps = [t for t in timestamps if t > window_start]

        if len(valid_timestamps) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - valid_timestamps[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds.",
                headers={"Retry-After": str(max(1, retry_after))},
            )

        valid_timestamps.append(now)
        self._memory_store[key] = valid_timestamps
        return True


# Convenience rate limiters for specific route tiers
auth_rate_limiter = SlidingWindowRateLimiter(requests=10, window_seconds=60, key_prefix="rl_auth")
invitation_rate_limiter = SlidingWindowRateLimiter(requests=15, window_seconds=60, key_prefix="rl_inv")
post_rate_limiter = SlidingWindowRateLimiter(requests=30, window_seconds=60, key_prefix="rl_post")
general_rate_limiter = SlidingWindowRateLimiter(requests=120, window_seconds=60, key_prefix="rl_gen")
