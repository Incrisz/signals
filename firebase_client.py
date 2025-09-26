"""Helpers for connecting to Firebase/Firestore and retrieving user events."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv(override=True)

FIREBASE_SECRET_ID = os.getenv("FIREBASE_SECRET_ID", "firebase-service-account")
FIREBASE_CREDENTIALS_FILE = os.getenv("FIREBASE_CREDENTIALS_FILE")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
FIREBASE_ROOT_COLLECTION = os.getenv("FIREBASE_ROOT_COLLECTION", "app_usage_events")
FIREBASE_EVENTS_SUBCOLLECTION = os.getenv("FIREBASE_EVENTS_SUBCOLLECTION", "events")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

_firestore_client = None


def _load_service_account() -> Dict[str, object]:
    if FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            return json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc

    if FIREBASE_CREDENTIALS_FILE:
        from pathlib import Path

        path = Path(FIREBASE_CREDENTIALS_FILE)
        if not path.exists():
            raise FileNotFoundError(f"Firebase credentials file not found at {path}")
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - surfaces missing optional dependency
        raise RuntimeError(
            "boto3 is required to load Firebase credentials from Secrets Manager"
        ) from exc

    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=FIREBASE_SECRET_ID)
    secret = response.get("SecretString")
    if not secret:
        raise RuntimeError(f"Secret {FIREBASE_SECRET_ID!r} did not contain a SecretString")
    return json.loads(secret)


def initialize_firestore():
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    import firebase_admin
    from firebase_admin import credentials, firestore

    service_account = _load_service_account()
    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred, {"projectId": service_account.get("project_id")})

    _firestore_client = firestore.client()
    return _firestore_client


def _coerce_datetime(value):
    if value is None:
        return None

    from datetime import datetime, timezone

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if hasattr(value, "to_datetime"):
        return value.to_datetime().replace(tzinfo=timezone.utc)

    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return value


def _normalize_event(raw: Dict[str, object], *, user_id: str, document_path: str, document_id: str, create_time, update_time) -> Dict[str, object]:
    event: Dict[str, object] = dict(raw)

    aliases = {
        "androidVersion": "android_version",
        "deviceModel": "device_model",
        "eventType": "event_type",
        "isScheduled": "is_scheduled",
        "lastTimeUsed": "last_time_used",
        "lastTimeUsedFormatted": "last_time_used_formatted",
        "packageName": "package_name",
        "phoneNumber": "phone_number",
        "sessionId": "session_id",
        "totalTimeInForeground": "total_time_in_foreground",
        "totalTimeInForegroundMinutes": "total_time_in_foreground_minutes",
        "totalTimeInForegroundMs": "total_time_in_foreground_ms",
        "userId": "user_id",
        "createdAt": "created_at",
        "updatedAt": "updated_at",
    }

    for src, dst in aliases.items():
        if src in raw and dst not in event:
            event[dst] = raw[src]

    event.setdefault("user_id", user_id)
    event.setdefault("id", document_id)
    event.setdefault("session_id", raw.get("sessionId") or document_id)
    event.setdefault("package_name", raw.get("packageName") or raw.get("appId") or raw.get("app"))
    event.setdefault("app", raw.get("app") or raw.get("packageName"))

    event["timestamp"] = _coerce_datetime(event.get("timestamp") or raw.get("timestamp"))
    event["created_at"] = _coerce_datetime(event.get("created_at") or create_time)
    event["updated_at"] = _coerce_datetime(event.get("updated_at") or update_time)

    event["document_path"] = document_path
    event["document_id"] = document_id

    return event


def fetch_user_events(user_id: str, *, limit: Optional[int] = None) -> List[Dict[str, object]]:
    client = initialize_firestore()
    collection = (
        client.collection(FIREBASE_ROOT_COLLECTION)
        .document(user_id)
        .collection(FIREBASE_EVENTS_SUBCOLLECTION)
    )

    if limit is not None:
        query = collection.limit(limit)
        documents = query.stream()
    else:
        documents = collection.stream()

    events: List[Dict[str, object]] = []
    for doc in documents:
        data = doc.to_dict() or {}
        normalized = _normalize_event(
            data,
            user_id=user_id,
            document_path=doc.reference.path,
            document_id=doc.id,
            create_time=doc.create_time,
            update_time=doc.update_time,
        )
        events.append(normalized)
    return events


def list_user_ids(*, limit: Optional[int] = None) -> List[str]:
    client = initialize_firestore()
    query = client.collection(FIREBASE_ROOT_COLLECTION)
    if limit is not None:
        query = query.limit(limit)
    return [doc.id for doc in query.stream()]


__all__ = ["fetch_user_events", "list_user_ids", "initialize_firestore"]
