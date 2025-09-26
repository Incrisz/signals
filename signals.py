"""FastAPI app exposing customer engagement signals backed by Postgres events."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Load environment variables from a local .env file when present.
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be configured (see .env.example).")

# Firebase credentials are stored in the environment for future use. They are not
# required while Firebase data lives in the Postgres events table, but the fields
# are declared here so the configuration surface is complete.
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_CREDENTIALS_FILE = os.getenv("FIREBASE_CREDENTIALS_FILE")

# Only this identifier needs to change when testing different users.
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "").strip() or None

_connection_pool: pool.SimpleConnectionPool | None = None
app = FastAPI(title="Customer Engagement Signals")


def _get_connection_pool() -> pool.SimpleConnectionPool:
    """Create (and reuse) a psycopg2 connection pool."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    return _connection_pool


def _execute_query(query: str, params: Iterable[Any]) -> List[Dict[str, Any]]:
    """Run a SELECT query and return rows as dictionaries."""
    conn_pool = _get_connection_pool()
    conn = conn_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn_pool.putconn(conn)


def _execute_scalar(query: str, params: Iterable[Any]) -> Any:
    """Execute a query that returns a single scalar value."""
    conn_pool = _get_connection_pool()
    conn = conn_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            result = cur.fetchone()
            return result[0] if result else None
    finally:
        conn_pool.putconn(conn)


def _try_parse_datetime(value: str, formats: Iterable[str]) -> Optional[datetime]:
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _event_time(event: Dict[str, Any]) -> Optional[datetime]:
    raw_last_used = event.get("last_time_used")
    if raw_last_used is not None:
        try:
            ts = float(raw_last_used)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass

    formatted_last_used = event.get("last_time_used_formatted")
    if isinstance(formatted_last_used, str) and formatted_last_used:
        parsed = _try_parse_datetime(
            formatted_last_used,
            ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"),
        )
        if parsed:
            return parsed

    raw_date = event.get("date")
    if isinstance(raw_date, str) and raw_date:
        parsed = _try_parse_datetime(raw_date, ("%Y-%m-%d", "%d/%m/%Y"))
        if parsed:
            return parsed

    created_at = event.get("created_at")
    if isinstance(created_at, datetime):
        return created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)

    updated_at = event.get("updated_at")
    if isinstance(updated_at, datetime):
        return updated_at if updated_at.tzinfo else updated_at.replace(tzinfo=timezone.utc)

    return None


def _minutes_played(event: Dict[str, Any]) -> float:
    for key in (
        "total_time_in_foreground_minutes",
        "total_time_in_foreground",
        "total_time_in_foreground_ms",
    ):
        value = event.get(key)
        if value is None:
            continue
        try:
            amount = float(value)
        except (TypeError, ValueError):
            continue
        if key == "total_time_in_foreground_ms":
            amount /= 60000.0
        if amount > 0:
            return amount
    return 0.0


def _resolve_user_ids(raw_user_ids: Optional[Sequence[str]]) -> List[str]:
    candidates: List[str] = []

    if raw_user_ids:
        for raw in raw_user_ids:
            if raw is None:
                continue
            for part in str(raw).split(","):
                cleaned = part.strip()
                if cleaned:
                    candidates.append(cleaned)
    elif DEFAULT_USER_ID:
        candidates.append(DEFAULT_USER_ID)

    if not candidates:
        raise HTTPException(
            status_code=400,
            detail="user_id is required; set DEFAULT_USER_ID in the environment or pass ?user_id=",
        )

    deduped: List[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            deduped.append(candidate)

    return deduped


def fetch_events(user_id: str) -> List[Dict[str, Any]]:
    query = """
        SELECT
            id,
            android_version,
            date,
            device_model,
            event_type,
            is_scheduled,
            last_time_used,
            last_time_used_formatted,
            package_name,
            phone_number,
            rank,
            session_id,
            total_time_in_foreground,
            total_time_in_foreground_minutes,
            total_time_in_foreground_ms,
            user_id,
            username,
            created_at,
            updated_at
        FROM public.events
        WHERE user_id = %s
        ORDER BY COALESCE(updated_at, created_at) DESC
    """
    return _execute_query(query, (user_id,))


def _fetch_events_by_user(user_ids: Sequence[str]) -> Dict[str, List[Dict[str, Any]]]:
    return {uid: fetch_events(uid) for uid in user_ids}


def goal_setting_completed(user_id: Optional[str]) -> bool:
    params: List[Any] = []
    where_clause = ""
    if user_id:
        where_clause = "WHERE u.id = %s"
        params.append(user_id)

    query = """
        SELECT EXISTS (
            SELECT 1
            FROM public.user_goals AS ug
            JOIN public.goals AS g ON g.id = ug."goalId"
            JOIN public.users AS u ON u.id = ug."userId"
            {where_clause}
        )
    """.format(where_clause=where_clause)

    return bool(_execute_scalar(query, params))


def customer_app_login_completed(events: List[Dict[str, Any]], *, min_minutes: float = 1.0) -> bool:
    return any(_minutes_played(event) >= min_minutes for event in events)


def customer_app_registration_completed(
    events: List[Dict[str, Any]], *, min_minutes: float = 4.0, min_weekly_sessions: int = 4
) -> Dict[str, Any]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
    max_minutes = max((_minutes_played(evt) for evt in events), default=0.0)
    recent_sessions: set[str] = set()
    for evt in events:
        event_time = _event_time(evt)
        if not event_time or event_time < cutoff:
            continue
        session_identifier = evt.get("session_id") or evt.get("id")
        if not session_identifier:
            continue
        recent_sessions.add(str(session_identifier))
    weekly_sessions = len(recent_sessions)
    used_app = bool(events)
    meets_minutes = max_minutes >= min_minutes
    meets_sessions = weekly_sessions >= min_weekly_sessions
    completed = used_app and (meets_minutes or meets_sessions)
    return {
        "event_count": len(events),
        "max_minutes": max_minutes,
        "weekly_sessions": weekly_sessions,
        "thresholds": {
            "min_foreground_minutes": min_minutes,
            "min_weekly_sessions": min_weekly_sessions,
        },
        "evaluation": {
            "used_app": used_app,
            "meets_minutes_threshold": meets_minutes,
            "meets_weekly_threshold": meets_sessions,
            "completed": completed,
        },
        "events": events,
    }


def customer_app_engaged(events: List[Dict[str, Any]]) -> bool:
    now = datetime.now(tz=timezone.utc)
    week_buckets = [set() for _ in range(3)]

    for event in events:
        minutes = _minutes_played(event)
        if minutes <= 0:
            continue
        event_time = _event_time(event)
        if not event_time:
            continue
        weeks_back = (now - event_time).days // 7
        if 0 <= weeks_back < len(week_buckets):
            session = str(event.get("session_id") or event.get("id") or "unknown-session")
            week_buckets[weeks_back].add(session)

    return all(bucket for bucket in week_buckets)


def customer_app_engagement_dropoff(events: List[Dict[str, Any]]) -> bool:
    now = datetime.now(tz=timezone.utc)
    current_week_active = False
    previous_week_active = False

    for event in events:
        minutes = _minutes_played(event)
        if minutes <= 0:
            continue
        event_time = _event_time(event)
        if not event_time:
            continue
        weeks_back = (now - event_time).days // 7
        if weeks_back == 0:
            current_week_active = True
        elif weeks_back == 1:
            previous_week_active = True

    return previous_week_active and not current_week_active


def customer_app_retained(events: List[Dict[str, Any]]) -> bool:
    now = datetime.now(tz=timezone.utc)
    week_buckets = [set() for _ in range(9)]

    for event in events:
        minutes = _minutes_played(event)
        if minutes <= 0:
            continue
        event_time = _event_time(event)
        if not event_time:
            continue
        weeks_back = (now - event_time).days // 7
        if 0 <= weeks_back < len(week_buckets):
            session = str(event.get("session_id") or event.get("id") or "unknown-session")
            week_buckets[weeks_back].add(session)

    return all(bucket for bucket in week_buckets)


def customer_app_retained_dropoff(events: List[Dict[str, Any]]) -> bool:
    now = datetime.now(tz=timezone.utc)
    week_buckets = [set() for _ in range(10)]

    for event in events:
        minutes = _minutes_played(event)
        if minutes <= 0:
            continue
        event_time = _event_time(event)
        if not event_time:
            continue
        weeks_back = (now - event_time).days // 7
        if 0 <= weeks_back < len(week_buckets):
            session = str(event.get("session_id") or event.get("id") or "unknown-session")
            week_buckets[weeks_back].add(session)

    previous_nine_active = all(week_buckets[i] for i in range(1, 10))
    current_week_inactive = not week_buckets[0]
    return previous_nine_active and current_week_inactive


def build_signal_summary(user_id: str) -> Dict[str, bool]:
    events = fetch_events(user_id)
    registration = customer_app_registration_completed(events)
    return {
        "goal_setting_completed": goal_setting_completed(user_id),
        "customer_app_registration_completed": registration["evaluation"]["completed"],
        "customer_app_login_completed": customer_app_login_completed(events),
        "customer_app_engaged": customer_app_engaged(events),
        "customer_app_engagement_dropoff": customer_app_engagement_dropoff(events),
        "customer_app_retained": customer_app_retained(events),
        "customer_app_retained_dropoff": customer_app_retained_dropoff(events),
    }


@app.get("/goal-setting-completed")
def goal_setting_endpoint(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        per_user = {uid: goal_setting_completed(uid) for uid in resolved_user_ids}
        value = next(iter(per_user.values())) if len(per_user) == 1 else per_user
        return {"goal_setting_completed": value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-registration-completed")
def registration_completed_endpoint(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        events_by_user = _fetch_events_by_user(resolved_user_ids)
        per_user = {
            uid: customer_app_registration_completed(events)["evaluation"]["completed"]
            for uid, events in events_by_user.items()
        }
        value = next(iter(per_user.values())) if len(per_user) == 1 else per_user
        return {"customer_app_registration_completed": value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-login-completed")
def login_completed_endpoint(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        events_by_user = _fetch_events_by_user(resolved_user_ids)
        per_user = {uid: customer_app_login_completed(events) for uid, events in events_by_user.items()}
        value = next(iter(per_user.values())) if len(per_user) == 1 else per_user
        return {"customer_app_login_completed": value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-engaged")
def engaged_endpoint(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        events_by_user = _fetch_events_by_user(resolved_user_ids)
        per_user = {uid: customer_app_engaged(events) for uid, events in events_by_user.items()}
        value = next(iter(per_user.values())) if len(per_user) == 1 else per_user
        return {"customer_app_engaged": value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-engagement-dropoff")
def engagement_dropoff_endpoint(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        events_by_user = _fetch_events_by_user(resolved_user_ids)
        per_user = {
            uid: customer_app_engagement_dropoff(events)
            for uid, events in events_by_user.items()
        }
        value = next(iter(per_user.values())) if len(per_user) == 1 else per_user
        return {"customer_app_engagement_dropoff": value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-retained")
def retained_endpoint(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        events_by_user = _fetch_events_by_user(resolved_user_ids)
        per_user = {uid: customer_app_retained(events) for uid, events in events_by_user.items()}
        value = next(iter(per_user.values())) if len(per_user) == 1 else per_user
        return {"customer_app_retained": value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-retained-dropoff")
def retained_dropoff_endpoint(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        events_by_user = _fetch_events_by_user(resolved_user_ids)
        per_user = {
            uid: customer_app_retained_dropoff(events)
            for uid, events in events_by_user.items()
        }
        value = next(iter(per_user.values())) if len(per_user) == 1 else per_user
        return {"customer_app_retained_dropoff": value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/signals")
def signals_summary(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        if len(resolved_user_ids) == 1:
            solo_id = resolved_user_ids[0]
            summary = build_signal_summary(solo_id)
            summary["user_id"] = solo_id
            return summary

        return {uid: build_signal_summary(uid) for uid in resolved_user_ids}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/milestones")
def milestones_summary(user_id: Optional[List[str]] = Query(default=None)) -> Dict[str, Any]:
    resolved_user_ids = _resolve_user_ids(user_id)
    try:
        from milestones import build_milestone_summary
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=f"milestones module unavailable: {exc}") from exc

    try:
        per_user: Dict[str, Dict[str, Any]] = {}
        for uid in resolved_user_ids:
            signal_summary = build_signal_summary(uid)
            milestones = build_milestone_summary(uid, signal_summary=signal_summary)
            per_user[uid] = {
                "user_id": uid,
                "signals": signal_summary,
                "milestones": milestones,
            }

        if len(per_user) == 1:
            return next(iter(per_user.values()))

        return per_user
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = [
    "app",
    "build_signal_summary",
    "customer_app_engaged",
    "customer_app_engagement_dropoff",
    "customer_app_login_completed",
    "customer_app_registration_completed",
    "customer_app_retained",
    "customer_app_retained_dropoff",
    "fetch_events",
    "goal_setting_completed",
]
