# Signals API

This repo exposes several FastAPI endpoints that analyse static Firebase engagement data and return simple boolean flags for registration, login, engagement, and retention milestones.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The service now listens on `http://127.0.0.1:8000`. Example calls:

- `GET /goal-setting-completed`
- `GET /customer-app-registration-completed`
- `GET /customer-app-login-completed`
- `GET /customer-app-engaged`
- `GET /customer-app-engagement-dropoff`
- `GET /customer-app-retained`
- `GET /customer-app-retained-dropoff`

All responses return a `{ "<endpoint>" : <bool> }`. The static engagement data is in `firebase.py`; update it (or use env vars) to simulate scenarios. Conditions:

- `goal-setting-completed`: user has at least one goal in Postgres (joined `user_goals` → `goals`).
- `customer-app-registration-completed`: user has ≥1 event, and either `totalTimeInForeground… ≥ 4` minutes or ≥4 sessions in the past 7 days.
- `customer-app-login-completed`: user has any event with ≥1 minute of foreground time.
- `customer-app-engaged`: user has ≥1 event with >0 minutes in each of the last 3 consecutive weeks.
- `customer-app-engagement-dropoff`: user had >0 minutes one week ago but no >0-minute events this week.
- `customer-app-retained`: user has ≥1 >0-minute event in each of the last 9 consecutive weeks.
- `customer-app-retained-dropoff`: user was active in each of the previous 9 weeks but has no >0-minute event this week.
