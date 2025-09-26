"""Milestone evaluation tied to customer engagement signals."""
from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional, Sequence, Set

from dotenv import load_dotenv
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# Ensure environment overrides match runtime configuration.
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be configured for milestone evaluation.")

_connection_pool: pool.SimpleConnectionPool | None = None


def _get_connection_pool() -> pool.SimpleConnectionPool:
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    return _connection_pool


def _execute_query(query: str, params: Iterable[object]) -> List[Dict[str, object]]:
    conn_pool = _get_connection_pool()
    conn = conn_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn_pool.putconn(conn)


def _relationship_to_tier(relationship: Optional[str]) -> Optional[str]:
    if relationship is None:
        return None
    lower = relationship.lower()
    if lower == "primary":
        return "tier1"
    if lower == "secondary":
        return "tier2"
    if lower == "tertiary":
        return "tier3"
    return None


def fetch_goal_subcategories_by_tier(user_id: str) -> Dict[str, Set[str]]:
    query = """
        SELECT
            ug."relationshipType" AS relationship,
            g."goalSubCategoryId" AS goal_subcategory_id
        FROM public.user_goals AS ug
        JOIN public.goals AS g ON g.id = ug."goalId"
        WHERE ug."userId" = %s
          AND g."goalSubCategoryId" IS NOT NULL
    """

    rows = _execute_query(query, (user_id,))
    tiers: Dict[str, Set[str]] = {"tier1": set(), "tier2": set(), "tier3": set()}

    for row in rows:
        tier = _relationship_to_tier(row.get("relationship"))
        subcategory = row.get("goal_subcategory_id")
        if tier and subcategory:
            tiers.setdefault(tier, set()).add(str(subcategory))

    return tiers


def fetch_event_goal_subcategories(user_id: str) -> Set[str]:
    query = """
        SELECT DISTINCT agsc."goalSubCategoriesId" AS goal_subcategory_id
        FROM public.events AS e
        JOIN public.apps AS a ON a."appId" = e.package_name
        JOIN public.app_goal_sub_categories AS agsc ON agsc."appsId" = a.id
        WHERE e.user_id = %s
    """

    rows = _execute_query(query, (user_id,))
    return {str(row["goal_subcategory_id"]) for row in rows if row.get("goal_subcategory_id")}


def _tier_has_matching_events(tiers: Dict[str, Set[str]], tier_key: str, event_subcategories: Set[str]) -> bool:
    tier_subcategories = tiers.get(tier_key, set())
    if not tier_subcategories:
        return False
    return bool(tier_subcategories & event_subcategories)


def build_milestone_summary(user_id: str, *, signal_summary: Optional[Dict[str, bool]] = None) -> Dict[str, bool]:
    if signal_summary is None:
        from signals import build_signal_summary  # Lazy import to avoid circular dependency at import time.

        signal_summary = build_signal_summary(user_id)

    goal_setting_completed = bool(signal_summary.get("goal_setting_completed"))
    registration_completed = bool(signal_summary.get("customer_app_registration_completed"))
    engaged = bool(signal_summary.get("customer_app_engaged"))
    engagement_dropoff = bool(signal_summary.get("customer_app_engagement_dropoff"))
    retained = bool(signal_summary.get("customer_app_retained"))
    retention_dropoff = bool(signal_summary.get("customer_app_retained_dropoff"))

    tiers = fetch_goal_subcategories_by_tier(user_id)
    event_subcategories = fetch_event_goal_subcategories(user_id)

    tier1_active = _tier_has_matching_events(tiers, "tier1", event_subcategories)
    tier2_active = _tier_has_matching_events(tiers, "tier2", event_subcategories)

    return {
        "goal_setting_complete": goal_setting_completed,
        "tier1_app_registered": goal_setting_completed and registration_completed and tier1_active,
        "tier2_app_registered": goal_setting_completed and registration_completed and tier2_active,
        "tier1_app_engaged": goal_setting_completed and engaged and tier1_active,
        "tier2_app_engaged": goal_setting_completed and engaged and tier2_active,
        "tier1_app_engagement_dropoff": goal_setting_completed and engagement_dropoff and tier1_active,
        "tier2_app_engagement_dropoff": goal_setting_completed and engagement_dropoff and tier2_active,
        "tier1_app_retained": goal_setting_completed and retained and tier1_active,
        "tier2_app_retained": goal_setting_completed and retained and tier2_active,
        "tier1_app_retention_dropoff": goal_setting_completed and retention_dropoff and tier1_active,
        "tier2_app_retention_dropoff": goal_setting_completed and retention_dropoff and tier2_active,
    }


def build_milestone_summaries(user_ids: Sequence[str]) -> Dict[str, Dict[str, bool]]:
    from signals import build_signal_summary  # Local import avoids circular reference.

    results: Dict[str, Dict[str, bool]] = {}
    for user_id in user_ids:
        summary = build_signal_summary(user_id)
        results[user_id] = build_milestone_summary(user_id, signal_summary=summary)
    return results


__all__ = [
    "build_milestone_summary",
    "build_milestone_summaries",
    "fetch_goal_subcategories_by_tier",
    "fetch_event_goal_subcategories",
]
