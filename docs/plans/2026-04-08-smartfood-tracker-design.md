# SmartFood Tracker Design

## Goal

Build a complete MVP for household food expiry management with low-friction input, an expiry dashboard, status transitions, and scheduled reminders.

## Context

The repository starts empty. The MVP should be easy to run locally, minimize deployment complexity, and keep external integrations optional so the system remains usable without LLM or push credentials.

## Recommended Approach

Use a single FastAPI application to host:

- REST APIs for item management and voice ingestion
- SQLite persistence via SQLAlchemy
- APScheduler-based daily reminder scanning
- A responsive static dashboard served by FastAPI

This keeps the system simple while preserving a clean enough module boundary to split frontend or background jobs later if needed.

## Architecture

### Backend

- `app/main.py` boots FastAPI, static files, API routers, and scheduler startup/shutdown hooks.
- `app/api/routes/items.py` exposes CRUD-style item routes.
- `app/services/voice_parser.py` handles LLM-backed or fallback parsing.
- `app/services/reminder_service.py` finds due reminders and dispatches notifications.
- `app/services/notifier.py` encapsulates webhook delivery and default mock logging behavior.
- `app/db/` contains SQLAlchemy engine, session handling, and model base.

### Frontend

- A single static dashboard page under `app/static/`.
- Uses plain HTML/CSS/JavaScript for low setup cost.
- Calls backend APIs directly for list refresh, item creation, voice input submission, filters, and status changes.

### Scheduler

- APScheduler runs inside the application process.
- A daily cron job scans `active` items for 30-day, 7-day, and 3-day reminder thresholds.
- Notification deduplication is handled in the application layer by tracking sent reminder stages.

## Data Model

Primary table: `food_items`

Fields:

- `id`: integer primary key
- `name`: required string
- `location`: required string with default `"未指定"`
- `entry_date`: datetime set on insert
- `expiry_date`: required date
- `status`: enum-like string: `active`, `consumed`, `discarded`
- `needs_confirmation`: boolean for fallback-parsed items requiring review
- `last_notified_stage`: nullable string storing the latest reminder milestone sent: `30d`, `7d`, `3d`

Computed response fields:

- `days_left`
- `urgency`

## API Design

### `POST /api/items`

Creates an item from a manual form payload.

### `POST /api/items/voice`

Accepts `{ "raw_text": "..." }`, parses text into structured fields, applies a 30-day fallback if the date cannot be confidently extracted, sets `needs_confirmation=true` when fallback is used, saves the item, and returns both persisted and parsed values.

### `GET /api/items`

Returns items sorted by `expiry_date` ascending. Supports `status` and `location` query parameters.

### `PUT /api/items/{id}/status`

Updates item status to `consumed` or `discarded`.

### `GET /api/locations`

Optional helper endpoint returning distinct known locations for frontend filtering.

## Voice Parsing Strategy

The parser uses two layers:

1. Configured LLM provider if credentials are available
2. Deterministic fallback parser if no credentials exist or parsing fails

Fallback behavior:

- Extract a likely food name and location using simple heuristics
- Default `location` to `"未指定"` if absent
- Default `expiry_date` to current date plus 30 days if no reliable date is found
- Mark `needs_confirmation=true`

This preserves usability even when third-party APIs are unavailable.

## Notification Strategy

The reminder job:

- selects only `active` items
- computes days until expiry using local date semantics
- triggers on exact milestones 30, 7, and 3
- skips already-notified stages by checking `last_notified_stage`

Notifier behavior:

- default mode logs outgoing reminder payloads
- optional webhook mode posts to a configured endpoint compatible with light push services

## Error Handling

- Validation errors return FastAPI standard 422 responses
- Missing items return 404
- LLM failures degrade to fallback parsing instead of failing the request
- Webhook failures are logged and do not crash the scheduler

## Testing Strategy

Use pytest with TDD for core behavior:

- item creation and sorted retrieval
- status updates removing items from active queries
- voice fallback parsing and `needs_confirmation`
- reminder milestone selection and deduplication

## Run Experience

Expected local developer flow:

- install dependencies
- run `uvicorn app.main:app --reload`
- open `/` for the dashboard
- use Swagger at `/docs` for API inspection
