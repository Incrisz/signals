"""Check if a user has spent at least one minute in the app using fake Firebase data."""
from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException

from firebase import FAKE_FIREBASE_EVENTS

USER_ID = ""
if FAKE_FIREBASE_EVENTS:
    candidate = FAKE_FIREBASE_EVENTS[0].get("userId")
    if isinstance(candidate, str):
        USER_ID = candidate.strip()
PACKAGE_NAME = os.getenv("PACKAGE_NAME_TEST", "").strip()
MIN_FOREGROUND_MINUTES = float(os.getenv("MIN_FOREGROUND_MINUTES", "1"))

app = FastAPI(title="Customer App Login (Fake Data)")


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


def _has_minimum_minutes(events: List[Dict[str, Any]]) -> bool:
    return any(_minutes_played(event) >= MIN_FOREGROUND_MINUTES for event in events)


def customer_app_login_completed() -> bool:
    if not USER_ID:
        raise ValueError("USER_ID_TEST must be set")

    user_events = [evt for evt in FAKE_FIREBASE_EVENTS if evt.get("userId") == USER_ID]
    if PACKAGE_NAME:
        user_events = [evt for evt in user_events if evt.get("packageName") == PACKAGE_NAME]

    return _has_minimum_minutes(user_events)


@app.get("/customer-app-login-completed")
def endpoint() -> Dict[str, bool]:
    try:
        return {"customer_app_login_completed": customer_app_login_completed()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["customer_app_login_completed", "app"]
