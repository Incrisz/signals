"""Aggregate FastAPI app exposing all customer engagement endpoints."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from goal_setting_completed import goal_setting_completed
from customer_app_engaged import customer_app_engaged
from Customer_app_engagement_dropoff import customer_app_engagement_dropoff
from customer_app_login_completed import customer_app_login_completed
from customer_app_registration_completed import customer_app_registration_completed
from customer_app_retained import customer_app_retained
from customer_app_retained_dropoff import customer_app_retained_dropoff

app = FastAPI(title="Customer App Engagement API")


@app.get("/goal-setting-completed")
def goal_completed() -> dict[str, bool]:
    try:
        return {"goal_setting_completed": goal_setting_completed()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-registration-completed")
def registration_completed() -> dict[str, bool]:
    try:
        result = customer_app_registration_completed()
        return {"customer_app_registration_completed": result["evaluation"]["completed"]}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-login-completed")
def login_completed() -> dict[str, bool]:
    try:
        return {"customer_app_login_completed": customer_app_login_completed()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-engaged")
def engaged() -> dict[str, bool]:
    try:
        return {"customer_app_engaged": customer_app_engaged()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-engagement-dropoff")
def engagement_dropoff() -> dict[str, bool]:
    try:
        return {"customer_app_engagement_dropoff": customer_app_engagement_dropoff()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-retained")
def retained() -> dict[str, bool]:
    try:
        return {"customer_app_retained": customer_app_retained()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/customer-app-retained-dropoff")
def retained_dropoff() -> dict[str, bool]:
    try:
        return {"customer_app_retained_dropoff": customer_app_retained_dropoff()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["app"]
