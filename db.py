"""Shared database utilities for Postgres access."""
from __future__ import annotations

import os
from typing import Iterable, List, Any, Optional

from dotenv import load_dotenv
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be configured (see .env.example).")

_connection_pool: pool.SimpleConnectionPool | None = None


def get_connection_pool() -> pool.SimpleConnectionPool:
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    return _connection_pool


def execute_query(query: str, params: Iterable[Any] | None = None) -> List[dict[str, Any]]:
    conn_pool = get_connection_pool()
    conn = conn_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params or ()))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn_pool.putconn(conn)


def execute_scalar(query: str, params: Iterable[Any] | None = None) -> Optional[Any]:
    conn_pool = get_connection_pool()
    conn = conn_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params or ()))
            result = cur.fetchone()
            return result[0] if result else None
    finally:
        conn_pool.putconn(conn)


__all__ = ["execute_query", "execute_scalar", "get_connection_pool"]
