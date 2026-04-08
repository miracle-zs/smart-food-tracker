# SmartFood Tracker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete SmartFood Tracker MVP with FastAPI, SQLite, APScheduler reminders, voice ingestion, and a responsive dashboard.

**Architecture:** A single FastAPI app serves REST APIs, static frontend assets, and an in-process scheduler. SQLAlchemy persists food items in SQLite, service modules encapsulate voice parsing and reminder delivery, and pytest covers the core business flows.

**Tech Stack:** Python, FastAPI, SQLAlchemy, APScheduler, pytest, HTML/CSS/JavaScript

---

### Task 1: Scaffold the application structure

**Files:**
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `app/db/__init__.py`
- Create: `app/db/base.py`
- Create: `app/db/session.py`
- Create: `app/api/__init__.py`
- Create: `app/api/routes/__init__.py`
- Create: `app/models/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/static/index.html`
- Create: `app/static/styles.css`
- Create: `app/static/app.js`
- Create: `requirements.txt`

**Step 1: Write the failing test**

Create a smoke test that imports the app and expects the root page and health route to exist.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_smoke.py -v`
Expected: FAIL because the app package and routes do not exist.

**Step 3: Write minimal implementation**

Add the application package, FastAPI bootstrap, static file serving, and a simple health endpoint.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app_smoke.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app tests requirements.txt
git commit -m "feat: scaffold smartfood tracker app"
```

### Task 2: Add persistence and manual item APIs

**Files:**
- Create: `app/models/food_item.py`
- Create: `app/schemas/item.py`
- Create: `app/api/routes/items.py`
- Modify: `app/main.py`
- Test: `tests/test_items_api.py`

**Step 1: Write the failing test**

Write tests for:
- creating an item via `POST /api/items`
- listing items via `GET /api/items`
- sorting by earliest expiry date first

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_items_api.py -v`
Expected: FAIL because item models and routes are missing.

**Step 3: Write minimal implementation**

Add SQLAlchemy model, session wiring, Pydantic schemas, and routes that persist and fetch food items in SQLite.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_items_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app tests
git commit -m "feat: add item CRUD APIs"
```

### Task 3: Add status transitions and filtering helpers

**Files:**
- Modify: `app/api/routes/items.py`
- Modify: `app/schemas/item.py`
- Test: `tests/test_item_status_and_filters.py`

**Step 1: Write the failing test**

Write tests for:
- updating item status to `consumed` and `discarded`
- filtering by `status`
- filtering by `location`
- excluding non-active items from active dashboard queries

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_item_status_and_filters.py -v`
Expected: FAIL because status update and filters are incomplete.

**Step 3: Write minimal implementation**

Extend list and update routes with filtering and computed response fields.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_item_status_and_filters.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app tests
git commit -m "feat: support item status transitions"
```

### Task 4: Add voice ingestion and parser fallback

**Files:**
- Create: `app/services/voice_parser.py`
- Modify: `app/api/routes/items.py`
- Test: `tests/test_voice_api.py`

**Step 1: Write the failing test**

Write tests for:
- successful voice ingestion with fallback date assignment
- `needs_confirmation=true` when no explicit date is found
- preserving explicit location when present

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_api.py -v`
Expected: FAIL because voice parsing route and service do not exist.

**Step 3: Write minimal implementation**

Implement the parser abstraction with deterministic fallback logic and wire `POST /api/items/voice`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_voice_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app tests
git commit -m "feat: add voice ingestion flow"
```

### Task 5: Add reminder scanning and notification service

**Files:**
- Create: `app/services/notifier.py`
- Create: `app/services/reminder_service.py`
- Create: `app/scheduler.py`
- Modify: `app/main.py`
- Test: `tests/test_reminders.py`

**Step 1: Write the failing test**

Write tests for:
- selecting only active items at 30, 7, and 3 day thresholds
- skipping already-sent reminder stages
- updating the stored notification stage after a send

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_reminders.py -v`
Expected: FAIL because reminder logic is missing.

**Step 3: Write minimal implementation**

Implement reminder selection, notifier abstraction, scheduler registration, and persistence updates.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_reminders.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app tests
git commit -m "feat: add reminder scheduler"
```

### Task 6: Build the dashboard frontend

**Files:**
- Modify: `app/static/index.html`
- Modify: `app/static/styles.css`
- Modify: `app/static/app.js`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

Write a delivery test that checks the root page serves the dashboard shell and references the frontend assets.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: FAIL because the dashboard shell is incomplete.

**Step 3: Write minimal implementation**

Implement a responsive dashboard with:
- manual form
- voice text form
- location filter
- expiry-sorted item list
- status action buttons
- inline pending-confirmation indicator

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app tests
git commit -m "feat: add dashboard frontend"
```

### Task 7: Final verification

**Files:**
- Modify: `README.md`

**Step 1: Write or update documentation**

Document setup, environment variables, run commands, and the fallback behavior for voice parsing and notifications.

**Step 2: Run full verification**

Run: `pytest -v`
Expected: all tests PASS

Run: `uvicorn app.main:app --reload`
Expected: app starts cleanly and serves `/`, `/docs`, and API routes

**Step 3: Commit**

```bash
git add README.md app tests docs/plans
git commit -m "docs: add smartfood tracker setup guide"
```
