# Signals API

FastAPI service that evaluates customer engagement signals using application events stored in Postgres. All signal logic now lives in `main.py`; map a different user by changing `DEFAULT_USER_ID` (see configuration below) or by passing `?user_id=` to each endpoint.

## Configuration

1. Copy `.env.example` to `.env`.
2. Populate `DATABASE_URL` with your Postgres connection string.
3. Optionally fill in the Firebase placeholders for future use.
4. Set `DEFAULT_USER_ID` to the user you want to inspect by default.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The service listens on `http://127.0.0.1:8000`. Append `?user_id=<uuid>` to target another user without editing the environment file.

## Available endpoints

- `GET /goal-setting-completed`
- `GET /customer-app-registration-completed`
- `GET /customer-app-login-completed`
- `GET /customer-app-engaged`
- `GET /customer-app-engagement-dropoff`
- `GET /customer-app-retained`
- `GET /customer-app-retained-dropoff`
- `GET /signals` (returns all of the above in a single payload)

Every endpoint returns a JSON payload with a single boolean flag (or, in the case of `/signals`, a dictionary of flags plus the resolved user id).

## Signal definitions

- **goal-setting-completed** – evaluates whether the user has at least one goal in `user_goals`/`goals`.
- **customer-app-registration-completed** – the user has events and either accumulates ≥4 minutes of foreground time in any event or logs ≥4 sessions in the past 7 days.
- **customer-app-login-completed** – the user has any event with ≥1 minute in the foreground.
- **customer-app-engaged** – the user has ≥1 event with foreground time in each of the last 3 consecutive weeks.
- **customer-app-engagement-dropoff** – the user was active last week but has no qualifying events this week.
- **customer-app-retained** – the user stays active in each of the last 9 consecutive weeks.
- **customer-app-retained-dropoff** – the user was active across the previous 9 weeks and became inactive this week.
- **signals** – convenience endpoint returning all flags for the chosen user.

These computations rely on the Postgres `events` table columns described in `schema.sql`.
