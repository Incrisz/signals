# Signals API

This repo exposes several FastAPI endpoints that analyse fake Firebase engagement data and return simple boolean flags for registration, login, engagement, and retention milestones.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The service now listens on `http://127.0.0.1:8000`. Example calls:

- `GET /customer-app-registration-completed`
- `GET /customer-app-login-completed`
- `GET /customer-app-engaged`
- `GET /customer-app-engagement-dropoff`
- `GET /customer-app-retained`
- `GET /customer-app-retained-dropoff`

All responses are simple JSON objects containing the corresponding boolean. Update `firebase.py` to tweak the sample event data or set environment variables (e.g. `PACKAGE_NAME_TEST`, `MIN_FOREGROUND_MINUTES`, `MIN_WEEKLY_SESSIONS`) before launching.
