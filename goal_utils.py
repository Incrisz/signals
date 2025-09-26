"""Helpers for mapping user goals to service app subcategories."""
from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Set

from db import execute_query


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

    rows = execute_query(query, (user_id,))
    tiers: Dict[str, Set[str]] = {"tier1": set(), "tier2": set(), "tier3": set()}

    for row in rows:
        relationship = (row.get("relationship") or "").lower()
        subcategory = row.get("goal_subcategory_id")
        if not subcategory:
            continue
        if relationship == "primary":
            tiers.setdefault("tier1", set()).add(str(subcategory))
        elif relationship == "secondary":
            tiers.setdefault("tier2", set()).add(str(subcategory))
        elif relationship == "tertiary":
            tiers.setdefault("tier3", set()).add(str(subcategory))

    return tiers


def map_packages_to_goal_subcategories(package_names: Sequence[str]) -> Dict[str, Set[str]]:
    packages = [pkg for pkg in {str(name) for name in package_names if name}]
    if not packages:
        return {}

    query = """
        SELECT
            a."appId" AS app_id,
            agsc."goalSubCategoriesId" AS goal_subcategory_id
        FROM public.apps AS a
        JOIN public.app_goal_sub_categories AS agsc ON agsc."appsId" = a.id
        WHERE a."appId" = ANY(%s)
    """

    rows = execute_query(query, (packages,))
    mapping: Dict[str, Set[str]] = {}
    for row in rows:
        app_id = row.get("app_id")
        subcategory = row.get("goal_subcategory_id")
        if not app_id or not subcategory:
            continue
        mapping.setdefault(str(app_id), set()).add(str(subcategory))
    return mapping


def flatten_tiers(tiers: Dict[str, Set[str]]) -> Set[str]:
    combined: Set[str] = set()
    for values in tiers.values():
        combined.update(values)
    return combined


__all__ = [
    "fetch_goal_subcategories_by_tier",
    "map_packages_to_goal_subcategories",
    "flatten_tiers",
]
