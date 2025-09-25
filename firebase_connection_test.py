"""FastAPI endpoint exposing a Firestore collection dump."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud.firestore_v1 import FieldFilter
except ImportError as exc:  # pragma: no cover - informative failure
    raise SystemExit("firebase_admin is not installed; run 'pip install firebase-admin google-cloud-firestore'") from exc


FIREBASE_CREDENTIALS_PATH = os.getenv(
    "FIREBASE_CREDENTIALS_PATH", "uniti-production-firebase-adminsdk-fbsvc-304a43723f.json"
)
FIREBASE_COLLECTION = os.getenv("FIREBASE_COLLECTION", "App_usage_event")
MAX_DOCUMENTS = int(os.getenv("FIREBASE_MAX_DOCUMENTS", "50"))


def initialise_app() -> None:
    cred_path = Path(FIREBASE_CREDENTIALS_PATH)
    if not cred_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {cred_path!s}")

    if not firebase_admin._apps:  # type: ignore[attr-defined]
        firebase_admin.initialize_app(credentials.Certificate(str(cred_path)))


def fetch_documents(limit: int = MAX_DOCUMENTS, user_id: Optional[str] = None) -> List[dict[str, Any]]:
    initialise_app()
    client = firestore.client()
    query = client.collection(FIREBASE_COLLECTION)
    if user_id:
        query = query.where(filter=FieldFilter("userId", "==", user_id.strip()))
    docs = query.limit(limit).stream()
    return [doc.to_dict() for doc in docs]


app = FastAPI(title="Firebase Inspection API")


@app.get("/firebase-dump")
def firebase_dump(limit: int = MAX_DOCUMENTS, user_id: Optional[str] = None) -> List[dict[str, Any]]:
    try:
        records = fetch_documents(limit=limit, user_id=user_id)
    except Exception as exc:  # pragma: no cover - surface connection issues
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return records


__all__ = ["app", "fetch_documents"]
