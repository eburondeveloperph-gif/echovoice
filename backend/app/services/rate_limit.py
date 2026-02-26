from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class Bucket:
    timestamps: deque[float] = field(default_factory=deque)


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, period_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self._buckets: dict[str, Bucket] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets.setdefault(key, Bucket())
        window_start = now - self.period_seconds

        while bucket.timestamps and bucket.timestamps[0] < window_start:
            bucket.timestamps.popleft()

        if len(bucket.timestamps) >= self.max_requests:
            return False

        bucket.timestamps.append(now)
        return True
