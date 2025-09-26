"""AWS Lambda entrypoint to compute signals and milestones from Firebase events."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from firebase_client import fetch_user_events, list_user_ids
from milestones import build_milestone_summary
from signals import build_signal_summary


def _parse_since(value: Any) -> Optional[datetime]:
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
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def _json_serial(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def handler(event: Optional[Dict[str, Any]], _context: Any) -> Dict[str, Any]:
    request = event or {}
    since = _parse_since(request.get("since") or request.get("since_timestamp"))

    user_ids = request.get("user_ids") or request.get("userIds")
    if not user_ids:
        try:
            user_id_limit = int(request.get("user_id_limit") or request.get("limit") or os.getenv("USER_ID_LIMIT", "50"))
        except ValueError:
            user_id_limit = 50
        user_ids = list_user_ids(limit=user_id_limit)

    if not user_ids:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No user IDs provided or discovered."}),
        }

    results: Dict[str, Dict[str, Any]] = {}
    for user_id in user_ids:
        events = fetch_user_events(user_id)
        if since is not None:
            filtered_events = []
            for evt in events:
                ts = evt.get("timestamp")
                if isinstance(ts, datetime) and ts < since:
                    continue
                if isinstance(ts, (int, float)):
                    ts_value = ts
                    if ts_value > 1e12:
                        ts_value /= 1000.0
                    if datetime.fromtimestamp(ts_value, tz=timezone.utc) < since:
                        continue
                filtered_events.append(evt)
            events = filtered_events

        signals_summary = build_signal_summary(user_id, events=events)
        milestone_summary = build_milestone_summary(user_id, signal_summary=signals_summary, events=events)
        results[user_id] = {
            "user_id": user_id,
            "event_count": len(events),
            "signals": signals_summary,
            "milestones": milestone_summary,
        }

    response_body = {
        "processed_user_ids": list(results.keys()),
        "results": results,
    }

    return {
        "statusCode": 200,
        "body": json.dumps(response_body, default=_json_serial),
    }


if __name__ == "__main__":  # Simple CLI helper for local execution.
    import argparse

    parser = argparse.ArgumentParser(description="Run the Lambda handler locally.")
    parser.add_argument("--user-id", dest="user_ids", action="append", help="User ID to evaluate (repeatable).")
    parser.add_argument("--since", dest="since", help="ISO timestamp or epoch for filtering events.")
    parser.add_argument("--limit", dest="limit", type=int, help="Fallback number of users to process when none provided.")
    args = parser.parse_args()

    payload: Dict[str, Any] = {}
    if args.user_ids:
        payload["user_ids"] = args.user_ids
    if args.since:
        payload["since"] = args.since
    if args.limit is not None:
        payload["limit"] = args.limit

    result = handler(payload, None)
    print(result["body"])
