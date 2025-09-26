# Signals & Milestones Lambda

Serverless-ready analyser that pulls engagement events from Firebase Firestore, reads goal metadata from Postgres, and produces both signal flags and milestone statuses per user. The core logic lives in `signals.py` and `milestones.py`, while `lambda_function.py` provides the AWS Lambda entrypoint.

## How it works (plain English)

- We pull every event for each user from the Firestore collection `app_usage_events/{userId}/events/{eventId}`.
- We check how long and how recently each user has been in the app to derive the engagement signals (login, retention, drop-offs, etc.).
- We read each user’s goal selections from Postgres and match event app IDs to goal subcategories to decide milestone progress.
- The Lambda handler loops through each user ID, runs the signal logic, runs the milestone logic, and returns a combined result set.

If you pass several user IDs (repeat the `user_ids` property or send a comma-separated list), the Lambda executes the same checks for each user and returns a per-user breakdown.

## Configuration

1. Copy `.env.example` to `.env` and populate:
   - `DATABASE_URL` for Postgres access (goal metadata).
   - One of `FIREBASE_CREDENTIALS_FILE`, `FIREBASE_SERVICE_ACCOUNT_JSON`, or `FIREBASE_SECRET_ID` (Secrets Manager) for Firebase credentials.
   - Optional overrides such as `FIREBASE_ROOT_COLLECTION`, `FIREBASE_EVENTS_SUBCOLLECTION`, `AWS_REGION`, and `USER_ID_LIMIT`.
2. Install dependencies: `pip install -r requirements.txt`.
3. For AWS Lambda, package the repository (or build a deployment layer) with these dependencies.

## Local execution

Use the CLI helper bundled with the Lambda handler:

```bash
python lambda_function.py --user-id 4fe1222a-94d9-45fd-b0f2-6856fcb1cb20
```

You can supply multiple `--user-id` values or let it fall back to `USER_ID_LIMIT` Firestore documents. Add `--since <ISO timestamp>` to filter events loaded in memory.

## Lambda handler shape

Invoke the function with a payload such as:

```json
{
  "user_ids": ["4fe1222a-94d9-45fd-b0f2-6856fcb1cb20", "another-user-id"],
  "since_timestamp": "2024-10-01T00:00:00Z"
}
```

Response body:

```json
{
  "processed_user_ids": ["4fe1222a-94d9-45fd-b0f2-6856fcb1cb20"],
  "results": {
    "4fe1222a-94d9-45fd-b0f2-6856fcb1cb20": {
      "user_id": "4fe1222a-94d9-45fd-b0f2-6856fcb1cb20",
      "event_count": 42,
      "signals": { "customer_app_login_completed": true, … },
      "milestones": { "tier1_app_registered": true, … }
    }
  }
}
```

## Signal definitions

- **goal-setting-completed** – user has at least one goal saved in Postgres (so we know which service app subcategories apply).
- **customer-app-registration-completed** – at least one service-app event that belongs to the user’s goal subcategories logs ≥4 minutes of foreground time **or** appears in four distinct sessions within the past 7 days.
- **customer-app-login-completed** – a goal-aligned service-app event records ≥1 minute in the foreground.
- **customer-app-engaged** – goal-aligned service-app events show foreground time (>0 minutes) in each of the last 3 consecutive weeks.
- **customer-app-engagement-dropoff** – the user had goal-aligned foreground time last week but none this week.
- **customer-app-retained** – goal-aligned service-app events show foreground time (>0 minutes) in each of the last 9 consecutive weeks.
- **customer-app-retained-dropoff** – the user stayed goal-aligned active for 9 straight weeks and then logged zero foreground time this week.
- **signals** – convenience grouping that returns all the above flags (plus metadata such as raw/service event counts) for each user.

## Milestone definitions

- **goal_setting_complete** – mirrors `goal-setting-completed`.
- **tier1_app_registered / tier2_app_registered** – goal selection is complete, the registration signal is true, and at least one recorded app event maps to the Tier 1 or Tier 2 goal subcategory.
- **tier1_app_engaged / tier2_app_engaged** – goal selection is complete, the engagement signal is true, and there are events mapped to the Tier 1 or Tier 2 goal subcategories.
- **tier1_app_engagement_dropoff / tier2_app_engagement_dropoff** – goal selection is complete, the engagement drop-off signal is true, and matching Tier 1 or Tier 2 subcategory events exist.
- **tier1_app_retained / tier2_app_retained** – goal selection is complete, the retention signal is true, and events exist for the Tier 1 or Tier 2 subcategories.
- **tier1_app_retention_dropoff / tier2_app_retention_dropoff** – goal selection is complete, the retention drop-off signal is true, and the user has events tied to the Tier 1 or Tier 2 subcategories.

Milestone evaluation uses `user_goals` and `goals` to understand Tier 1/Tier 2 selections, and joins `apps` → `app_goal_sub_categories` to confirm the user interacted with an app that belongs to the relevant subcategory.

## Packaging tips

- Bundle `psycopg2-binary`, `firebase-admin`, `google-cloud-firestore`, `boto3`, and their native dependencies with your Lambda deployment package or layer.
- Ensure the Lambda role can access Secrets Manager (if you rely on `FIREBASE_SECRET_ID`) and the target Postgres instance.
