"""Signal calculations using Firebase events and goal-aware service app filters."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from firebase_client import fetch_user_events
from goal_utils import (
    fetch_goal_subcategories_by_tier,
    flatten_tiers,
    map_packages_to_goal_subcategories,
)
from db import execute_scalar


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if isinstance(value, str):
        formats = (
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
        )
        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _event_time(event: Dict[str, Any]) -> Optional[datetime]:
    candidate_keys = (
        "timestamp",
        "event_timestamp",
        "last_time_used",
        "created_at",
        "updated_at",
        "date",
        "last_time_used_formatted",
    )
    for key in candidate_keys:
        candidate = event.get(key)
        parsed = _parse_datetime(candidate)
        if parsed is not None:
            return parsed
    return None


def _minutes_played(event: Dict[str, Any]) -> float:
    keys = (
        "total_time_in_foreground_minutes",
        "totalTimeInForegroundMinutes",
        "total_time_in_foreground",
        "totalTimeInForeground",
        "total_time_in_foreground_ms",
        "totalTimeInForegroundMs",
    )
    for key in keys:
        value = event.get(key)
        if value is None:
            continue
        try:
            amount = float(value)
        except (TypeError, ValueError):
            continue
        if key.endswith("Ms") or key.endswith("_ms"):
            amount /= 60000.0
        if amount > 0:
            return amount
    return 0.0


def fetch_events(user_id: str, *, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    return fetch_user_events(user_id, limit=limit)


def _filter_service_events(
    user_id: str,
    events: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, set[str]], set[str]]:
    tiers = fetch_goal_subcategories_by_tier(user_id)
    user_subcategories = flatten_tiers(tiers)
    if not user_subcategories:
        return [], tiers, user_subcategories

    package_names = {
        str(event.get("package_name") or event.get("app") or "")
        for event in events
        if event.get("package_name") or event.get("app")
    }
    package_map = map_packages_to_goal_subcategories(list(package_names))

    filtered: List[Dict[str, Any]] = []
    for event in events:
        package = str(event.get("package_name") or event.get("app") or "")
        subcategories = package_map.get(package, set())
        if not subcategories:
            continue
        if not (subcategories & user_subcategories):
            continue
        event_copy = dict(event)
        event_copy["service_goal_subcategories"] = list(subcategories)
        filtered.append(event_copy)

    return filtered, tiers, user_subcategories


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

    return bool(execute_scalar(query, params))


def customer_app_login_completed(events: Sequence[Dict[str, Any]], *, min_minutes: float = 1.0) -> bool:
    return any(_minutes_played(event) >= min_minutes for event in events)


def customer_app_registration_completed(
    events: Sequence[Dict[str, Any]], *, min_minutes: float = 4.0, min_weekly_sessions: int = 4
) -> Dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=7)

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
    }


def customer_app_engaged(events: Sequence[Dict[str, Any]]) -> bool:
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


def customer_app_engagement_dropoff(events: Sequence[Dict[str, Any]]) -> bool:
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


def customer_app_retained(events: Sequence[Dict[str, Any]]) -> bool:
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


def customer_app_retained_dropoff(events: Sequence[Dict[str, Any]]) -> bool:
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


def build_signal_summary(
    user_id: str,
    *,
    events: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    raw_events = list(events) if events is not None else fetch_events(user_id)
    service_events, tiers, _ = _filter_service_events(user_id, raw_events)

    registration = customer_app_registration_completed(service_events)

    return {
        "user_id": user_id,
        "raw_event_count": len(raw_events),
        "service_event_count": len(service_events),
        "goal_setting_completed": goal_setting_completed(user_id),
        "customer_app_registration_completed": registration["evaluation"]["completed"],
        "customer_app_login_completed": customer_app_login_completed(service_events),
        "customer_app_engaged": customer_app_engaged(service_events),
        "customer_app_engagement_dropoff": customer_app_engagement_dropoff(service_events),
        "customer_app_retained": customer_app_retained(service_events),
        "customer_app_retained_dropoff": customer_app_retained_dropoff(service_events),
        "registration_metrics": registration,
        "service_goal_tiers": {tier: list(values) for tier, values in tiers.items()},
    }


def build_signal_summaries(user_ids: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    return {user_id: build_signal_summary(user_id) for user_id in user_ids}


__all__ = [
    "build_signal_summary",
    "build_signal_summaries",
    "customer_app_engaged",
    "customer_app_engagement_dropoff",
    "customer_app_login_completed",
    "customer_app_registration_completed",
    "customer_app_retained",
    "customer_app_retained_dropoff",
    "fetch_events",
    "goal_setting_completed",
]
