"""Detect whether weekly engagement dropped off after a previously active week."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from firebase import FAKE_FIREBASE_EVENTS

app = FastAPI(title="Customer App Engagement Drop-off (Fake Data)")


def _event_time(event: Dict[str, Any]) -> datetime | None:
    candidate = event.get("timestamp")
    if candidate is not None:
        try:
            ts = float(candidate)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (TypeError, ValueError, OSError):  # pragma: no cover
            pass

    candidate = event.get("date")
    if isinstance(candidate, str) and candidate:
        try:
            return datetime.strptime(candidate, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:  # pragma: no cover
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


def customer_app_engagement_dropoff() -> bool:
    now = datetime.now(tz=timezone.utc)

    current_week_active = False
    previous_week_active = False

    for event in FAKE_FIREBASE_EVENTS:
        minutes = _minutes_played(event)
        if minutes <= 0:
            continue

        event_time = _event_time(event)
        if event_time is None:
            continue

        delta = now - event_time
        weeks_back = delta.days // 7

        if weeks_back == 0:
            current_week_active = True
        elif weeks_back == 1:
            previous_week_active = True

    return previous_week_active and not current_week_active


@app.get("/customer-app-engagement-dropoff")
def endpoint() -> Dict[str, bool]:
    try:
        return {"customer_app_engagement_dropoff": customer_app_engagement_dropoff()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["customer_app_engagement_dropoff", "app"]
