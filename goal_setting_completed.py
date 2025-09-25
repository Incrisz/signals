"""Access the goal-tracking database and expose an API endpoint returning a goal-selection flag."""
from __future__ import annotations

import os
from typing import Dict

from fastapi import FastAPI, HTTPException
from psycopg2 import pool


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:SaUhIuPOZADHxSuVxOHYnWITglKtlFyB@shortline.proxy.rlwy.net:17803/railway",
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be provided to connect to PostgreSQL")


# Change this value to test other users; set to None (or empty string) to check every user.
USER_ID_TEST: str | None = os.getenv("USER_ID_TEST") or "4fe1222a-94d9-45fd-b0f2-6856fcb1cb20"
if USER_ID_TEST:
    USER_ID_TEST = USER_ID_TEST.strip() or None


_connection_pool: pool.SimpleConnectionPool | None = None


def get_connection_pool() -> pool.SimpleConnectionPool:
    """Lazily create (and reuse) a psycopg2 connection pool."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    return _connection_pool


def goal_setting_completed() -> bool:
    """Return True when at least one goal exists for the targeted user(s).

    Uses `USER_ID_TEST` to optionally scope the check to a particular user id.
    """

    where_clause = ""
    params: list[str] = []
    if USER_ID_TEST:
        where_clause = "WHERE u.id = %s"
        params.append(USER_ID_TEST)

    query = """
        SELECT EXISTS (
            SELECT 1
            FROM public.user_goals AS ug
            JOIN public.goals AS g ON g.id = ug."goalId"
            JOIN public.users AS u ON u.id = ug."userId"
    """

    if where_clause:
        query += f"            {where_clause}\n"

    query += "        )"

    conn_pool = get_connection_pool()
    conn = conn_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            (result,) = cur.fetchone()
    finally:
        conn_pool.putconn(conn)

    return bool(result)


# Uncomment the helper below if you need the detailed payload of users and their goals.
# from typing import Any, List  # add back near the top if you enable this block
# from psycopg2.extras import RealDictCursor  # also re-introduce this import
# def goal_setting_completed_details() -> List[Dict[str, Any]]:
#     base_query = """
#         SELECT
#             row_to_json(u) AS user,
#             row_to_json(g) AS goal
#         FROM public.users AS u
#         LEFT JOIN public.user_goals AS ug ON ug."userId" = u.id
#         LEFT JOIN public.goals AS g ON g.id = ug."goalId"
#     """
#
#     params: List[Any] = []
#     filter_clause = ""
#     if USER_ID_TEST:
#         filter_clause = "WHERE u.id = %s"
#         params.append(USER_ID_TEST)
#
#     query = "\n".join(part for part in (base_query, filter_clause, "ORDER BY u.id") if part)
#
#     conn_pool = get_connection_pool()
#     conn = conn_pool.getconn()
#     try:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(query, params)
#             rows = cur.fetchall()
#     finally:
#         conn_pool.putconn(conn)
#
#     users: Dict[str, Dict[str, Any]] = {}
#     for row in rows:
#         user = row["user"]
#         goal = row["goal"]
#         user_id = user.get("id")
#
#         if user_id is None:
#             continue
#
#         bucket = users.setdefault(user_id, {"user": user, "goals": [], "hasGoals": False})
#         if goal is not None:
#             bucket["goals"].append(dict(goal))
#             bucket["hasGoals"] = True
#
#     return list(users.values())


app = FastAPI(title="Goal Setting API")


@app.get("/goal-setting-completed")
def users_with_goals() -> Dict[str, bool]:
    try:
        return {"goals_selection_completed": goal_setting_completed()}
    except Exception as exc:  # pragma: no cover - defensive HTTP error mapping
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["goal_setting_completed", "app"]
