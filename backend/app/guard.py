"""Abuse guards for the public deployment: in-memory sliding-window rate limits.

One Render instance serves the API, so process memory is enough; limits reset on restart.
Keyed by client IP (first X-Forwarded-For entry behind Render's proxy).
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

HOUR = 3600
DAY = 24 * HOUR


def _limit(name: str, default: int) -> int:
    try:
        return int(os.getenv(name) or default)
    except ValueError:
        return default


class SlidingWindow:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window: int) -> bool:
        """Records one hit; False when the key already had `limit` hits in the window."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


windows = SlidingWindow()


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _too_many() -> HTTPException:
    return HTTPException(429, "Too many requests from here. Please try again later. / অনেক বেশি অনুরোধ; একটু পরে চেষ্টা করুন।")


def limit_scan(request: Request) -> None:
    """Photo reading spends AI credits: per-IP per hour, plus a global daily ceiling."""
    if not windows.hit(f"scan:{client_ip(request)}", _limit("SCAN_LIMIT_PER_IP", 10), HOUR):
        raise _too_many()
    if not windows.hit("scan:*", _limit("SCAN_LIMIT_GLOBAL", 200), DAY):
        raise _too_many()


def limit_new_patient(request: Request) -> None:
    if not windows.hit(f"patient:{client_ip(request)}", _limit("PATIENT_LIMIT_PER_IP", 5), HOUR):
        raise _too_many()


def limit_writes(request: Request) -> None:
    if not windows.hit(f"write:{client_ip(request)}", _limit("WRITE_LIMIT_PER_IP", 120), HOUR):
        raise _too_many()
