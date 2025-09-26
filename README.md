# Signals API

FastAPI service that evaluates customer engagement signals using application events stored in Postgres. All signal logic now lives in `signals.py`; map a different user by changing `DEFAULT_USER_ID` (see configuration below) or by passing `?user_id=` to each endpoint.

## How it works (plain English)

- The API looks up a user ID in the `events` table and gathers **every** event tied to that user.
- It checks how long the app was open and when that happened to decide if the user has logged in, stayed active, or dropped off.
- It also queries the goals tables to see if the user has set up at least one goal.
- Each endpoint turns those checks into a simple yes/no answer so non-technical teammates can read them quickly.
- If you send several user IDs (repeat the `user_id` query parameter or supply a comma-separated list), the service runs the same checks for each user and returns a per-user breakdown.

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
uvicorn signals:app --reload
```

The service listens on `http://127.0.0.1:8000`. Append `?user_id=<uuid>` to target another user, or pass multiple IDs (`?user_id=<uuid1>&user_id=<uuid2>` or `?user_id=<uuid1>,<uuid2>`) to receive results for each user in one response.

## Available endpoints

- `GET /signals` (returns all signal flags in a single payload)
- `GET /milestones` (returns signal flags plus milestone evaluations)

- `GET /goal-setting-completed`
- `GET /customer-app-registration-completed`
- `GET /customer-app-login-completed`
- `GET /customer-app-engaged`
- `GET /customer-app-engagement-dropoff`
- `GET /customer-app-retained`
- `GET /customer-app-retained-dropoff`

Every endpoint returns a JSON payload with a single boolean flag (or, in the case of `/signals`, a dictionary of flags plus the resolved user id).

## Signal definitions

- **goal-setting-completed** – says “yes” when the user has at least one goal saved in the goals tables.
- **customer-app-registration-completed** – says “yes” when the user has used the app and either spent about 4 minutes inside or opened it in four different sessions during the last week.
- **customer-app-login-completed** – says “yes” if any event shows the user spent at least a minute in the app.
- **customer-app-engaged** – says “yes” if the user was active (any foreground time) every week for the past three weeks.
- **customer-app-engagement-dropoff** – says “yes” if the user was active last week but not this week.
- **customer-app-retained** – says “yes” if the user stayed active every week for the past nine weeks.
- **customer-app-retained-dropoff** – says “yes” if the user was active for nine straight weeks and then stopped this week.
- **signals** – returns all of the above flags together for the selected user.
- **milestones** – bundles the signal output together with milestone flags (see below) for each requested user.

These computations rely on the Postgres `events` table columns described in `schema.sql`.

## Milestone definitions

- **goal_setting_complete** – mirrors `goal-setting-completed`.
- **tier1_app_registered / tier2_app_registered** – goal selection is complete, the registration signal is true, and at least one recorded app event maps to the Tier 1 or Tier 2 goal subcategory.
- **tier1_app_engaged / tier2_app_engaged** – goal selection is complete, the engagement signal is true, and there are events mapped to the Tier 1 or Tier 2 goal subcategories.
- **tier1_app_engagement_dropoff / tier2_app_engagement_dropoff** – goal selection is complete, the engagement drop-off signal is true, and matching Tier 1 or Tier 2 subcategory events exist.
- **tier1_app_retained / tier2_app_retained** – goal selection is complete, the retention signal is true, and events exist for the Tier 1 or Tier 2 subcategories.
- **tier1_app_retention_dropoff / tier2_app_retention_dropoff** – goal selection is complete, the retention drop-off signal is true, and the user has events tied to the Tier 1 or Tier 2 subcategories.

Milestone evaluation uses `user_goals` and `goals` to understand the Tier 1 / Tier 2 selections, and joins `events` → `apps` → `app_goal_sub_categories` to confirm the user interacted with an app that belongs to the relevant subcategory.
