"""Simple app-engagement check backed by fake Firebase data."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException

from firebase import FAKE_FIREBASE_EVENTS

# Default to the first user present in the fake Firebase payload.
USER_ID = ""
if FAKE_FIREBASE_EVENTS:
    candidate = FAKE_FIREBASE_EVENTS[0].get("userId")
    if isinstance(candidate, str):
        USER_ID = candidate.strip()
PACKAGE_NAME = os.getenv("PACKAGE_NAME_TEST", "").strip()
MIN_FOREGROUND_MINUTES = float(os.getenv("MIN_FOREGROUND_MINUTES", "4"))
MIN_WEEKLY_SESSIONS = int(os.getenv("MIN_WEEKLY_SESSIONS", "4"))

app = FastAPI(title="Customer App Registration (Fake Data)")


def _event_time(event: Dict[str, Any]) -> datetime:
    ts = event.get("timestamp")
    if ts is not None:
        try:
            ts = float(ts)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (TypeError, ValueError):
            pass
    date_str = event.get("date")
    if isinstance(date_str, str) and date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(tz=timezone.utc)


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


def _evaluate(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
    max_minutes = max((_minutes_played(evt) for evt in events), default=0.0)
    recent_sessions = {
        evt.get("sessionId")
        for evt in events
        if isinstance(evt.get("sessionId"), str)
        and evt["sessionId"].strip()
        and _event_time(evt) >= cutoff
    }
    weekly_sessions = len(recent_sessions)
    used_app = bool(events)
    meets_minutes = max_minutes >= MIN_FOREGROUND_MINUTES
    meets_sessions = weekly_sessions >= MIN_WEEKLY_SESSIONS
    completed = used_app and (meets_minutes or meets_sessions)
    return {
        "event_count": len(events),
        "max_minutes": max_minutes,
        "weekly_sessions": weekly_sessions,
        "evaluation": {
            "used_app": used_app,
            "meets_minutes_threshold": meets_minutes,
            "meets_weekly_threshold": meets_sessions,
            "completed": completed,
        },
        "events": events,
    }


def customer_app_registration_completed() -> Dict[str, Any]:
    if not USER_ID:
        raise ValueError("USER_ID_TEST must be set")

    user_events = [evt for evt in FAKE_FIREBASE_EVENTS if evt.get("userId") == USER_ID]
    if PACKAGE_NAME:
        user_events = [evt for evt in user_events if evt.get("packageName") == PACKAGE_NAME]

    metrics = _evaluate(user_events)
    return {
        "user_id": USER_ID,
        "package_name": PACKAGE_NAME or "*",
        "thresholds": {
            "min_foreground_minutes": MIN_FOREGROUND_MINUTES,
            "min_weekly_sessions": MIN_WEEKLY_SESSIONS,
        },
        **metrics,
    }


@app.get("/customer-app-registration-completed")
def endpoint() -> Dict[str, Any]:
    try:
        result = customer_app_registration_completed()
        return {"customer_app_registration_completed": result["evaluation"]["completed"]}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["customer_app_registration_completed", "app"]
