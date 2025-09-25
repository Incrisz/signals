"""Detect a drop-off after nine consecutive active weeks."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from firebase import FAKE_FIREBASE_EVENTS

app = FastAPI(title="Customer App Retained Drop-off (Fake Data)")


def _event_time(event: Dict[str, Any]) -> datetime | None:
    candidate = event.get("timestamp")
    if candidate is not None:
        try:
            ts = float(candidate)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass

    candidate = event.get("date")
    if isinstance(candidate, str) and candidate:
        try:
            return datetime.strptime(candidate, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    return None


def _minutes_played(event: Dict[str, Any]) -> float:
    for key in ("totalTimeInForegroundMinutes", "totalTimeInForeground", "totalTimeInForegroundMs"):
        value = event.get(key)
        if value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if key == "totalTimeInForegroundMs":
            value /= 60000.0
        if value > 0:
            return value
    return 0.0


def customer_app_retained_dropoff() -> bool:
    now = datetime.now(tz=timezone.utc)
    week_buckets = [set() for _ in range(10)]  # current week + previous 9 weeks

    for event in FAKE_FIREBASE_EVENTS:
        minutes = _minutes_played(event)
        if minutes <= 0:
            continue

        event_time = _event_time(event)
        if event_time is None:
            continue

        delta = now - event_time
        weeks_back = delta.days // 7

        if 0 <= weeks_back < len(week_buckets):
            session_id = event.get("sessionId") or event.get("id") or "unknown-session"
            week_buckets[weeks_back].add(str(session_id))

    previous_nine_active = all(week_buckets[i] for i in range(1, 10))
    current_week_inactive = not week_buckets[0]

    return previous_nine_active and current_week_inactive


@app.get("/customer-app-retained-dropoff")
def endpoint() -> Dict[str, bool]:
    try:
        return {"customer_app_retained_dropoff": customer_app_retained_dropoff()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["customer_app_retained_dropoff", "app"]
