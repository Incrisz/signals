"""Milestone evaluation tied to customer engagement signals."""
from __future__ import annotations

from typing import Dict, Optional, Sequence

from goal_utils import fetch_goal_subcategories_by_tier, map_packages_to_goal_subcategories


def fetch_event_goal_subcategories(events: Sequence[Dict[str, object]]) -> Dict[str, set[str]]:
    package_names = {
        str(evt.get("package_name") or evt.get("app") or "")
        for evt in events
        if evt.get("package_name") or evt.get("app")
    }
    if not package_names:
        return {}
    return map_packages_to_goal_subcategories(list(package_names))


def _tier_has_matching_events(user_subcategories: set[str], event_subcategories: set[str]) -> bool:
    if not user_subcategories or not event_subcategories:
        return False
    return bool(user_subcategories & event_subcategories)


def build_milestone_summary(
    user_id: str,
    *,
    signal_summary: Optional[Dict[str, bool]] = None,
    events: Optional[Sequence[Dict[str, object]]] = None,
) -> Dict[str, bool]:
    from signals import build_signal_summary, fetch_events  # Local import to avoid circular dependency.

    raw_events = list(events) if events is not None else fetch_events(user_id)
    if signal_summary is None:
        signal_summary = build_signal_summary(user_id, events=raw_events)

    goal_setting_completed = bool(signal_summary.get("goal_setting_completed"))
    registration_completed = bool(signal_summary.get("customer_app_registration_completed"))
    engaged = bool(signal_summary.get("customer_app_engaged"))
    engagement_dropoff = bool(signal_summary.get("customer_app_engagement_dropoff"))
    retained = bool(signal_summary.get("customer_app_retained"))
    retention_dropoff = bool(signal_summary.get("customer_app_retained_dropoff"))

    tiers = fetch_goal_subcategories_by_tier(user_id)
    tier1 = tiers.get("tier1", set())
    tier2 = tiers.get("tier2", set())

    package_map = fetch_event_goal_subcategories(raw_events)
    event_subcategories = set().union(*package_map.values()) if package_map else set()

    tier1_active = _tier_has_matching_events(tier1, event_subcategories)
    tier2_active = _tier_has_matching_events(tier2, event_subcategories)

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
    from signals import build_signal_summary, fetch_events  # Deferred import avoids circular reference.

    results: Dict[str, Dict[str, bool]] = {}
    for user_id in user_ids:
        events = fetch_events(user_id)
        summary = build_signal_summary(user_id, events=events)
        results[user_id] = build_milestone_summary(user_id, signal_summary=summary, events=events)
    return results


__all__ = [
    "build_milestone_summary",
    "build_milestone_summaries",
    "fetch_event_goal_subcategories",
]
