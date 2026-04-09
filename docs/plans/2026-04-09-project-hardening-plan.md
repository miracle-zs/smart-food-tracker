# SmartFood Tracker Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the main remaining product gaps for SmartFood Tracker by adding real device/webhook ingestion, stronger Chinese date parsing, confirmation/edit flows, and production-oriented notification adapters.

**Architecture:** Keep the current single FastAPI application, but extend it in four bounded slices: ingestion adapters, voice/date parsing, item confirmation APIs plus frontend editing, and notification provider adapters. Each slice remains independently testable and reuses the existing SQLAlchemy and static-dashboard structure.

**Tech Stack:** Python, FastAPI, SQLAlchemy, APScheduler, pytest, HTML/CSS/JavaScript

**Status:** Tasks 1-4 were implemented on this branch before the final integration pass. Task 5 now records the documentation refresh and the full-suite verification for the hardened branch.

---

### Task 1: Add inbound webhook ingestion for XiaoAi-style text payloads

**Files:**
- Modify: `app/api/routes/items.py`
- Modify: `app/schemas/item.py`
- Test: `tests/test_voice_api.py`
- Test: `tests/test_webhook_ingestion.py`

**Step 1: Write the failing test**

Add a test covering a webhook-oriented endpoint that accepts a permissive payload with a text field from XiaoAi-style integrations and routes it through the existing voice ingestion flow.

**Step 2: Run test to verify it fails**

Run: `../../.venv/bin/pytest tests/test_webhook_ingestion.py -v`
Expected: FAIL because the endpoint and schema do not exist.

**Step 3: Write minimal implementation**

Add a new endpoint under `app/api/items/voice/webhook` that:
- accepts a flexible payload containing raw text in common fields such as `text`, `raw_text`, or nested `query`
- normalizes the inbound content
- reuses the existing voice parser and persistence flow
- returns a compact success payload suitable for webhook integrations

**Step 4: Run test to verify it passes**

Run: `../../.venv/bin/pytest tests/test_webhook_ingestion.py tests/test_voice_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/api/routes/items.py app/schemas/item.py tests/test_voice_api.py tests/test_webhook_ingestion.py
git commit -m "feat: add webhook voice ingestion endpoint"
```

### Task 2: Improve Chinese natural-language date parsing fallback

**Files:**
- Modify: `app/services/voice_parser.py`
- Test: `tests/test_voice_parser_service.py`
- Test: `tests/test_voice_api.py`

**Step 1: Write the failing test**

Add tests for fallback parsing of:
- `今年10月底过期`
- `3天后过期`
- `明天过期`

**Step 2: Run test to verify it fails**

Run: `../../.venv/bin/pytest tests/test_voice_parser_service.py tests/test_voice_api.py -v`
Expected: FAIL because the fallback parser only supports `YYYY-MM-DD`.

**Step 3: Write minimal implementation**

Extend fallback parsing logic to support:
- relative day expressions: `今天`, `明天`, `后天`, `N天后`
- current-year end-of-month phrases such as `今年10月底`
- current-year month-day phrases such as `10月31日`

Preserve existing LLM-first behavior and only apply this logic in fallback mode.

**Step 4: Run test to verify it passes**

Run: `../../.venv/bin/pytest tests/test_voice_parser_service.py tests/test_voice_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/voice_parser.py tests/test_voice_parser_service.py tests/test_voice_api.py
git commit -m "feat: improve Chinese expiry date parsing"
```

### Task 3: Add confirmation and editing flow for pending items

**Files:**
- Modify: `app/api/routes/items.py`
- Modify: `app/schemas/item.py`
- Modify: `app/static/index.html`
- Modify: `app/static/styles.css`
- Modify: `app/static/app.js`
- Test: `tests/test_item_confirmation_api.py`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

Add tests for:
- updating item name, location, and expiry date
- clearing `needs_confirmation` after explicit confirmation
- frontend shell containing a lightweight edit/confirm panel

**Step 2: Run test to verify it fails**

Run: `../../.venv/bin/pytest tests/test_item_confirmation_api.py tests/test_frontend_delivery.py -v`
Expected: FAIL because the edit API and frontend affordances do not exist.

**Step 3: Write minimal implementation**

Add:
- `PUT /api/items/{id}` for editing active items
- `POST /api/items/{id}/confirm` to clear `needs_confirmation`
- frontend controls to open an edit state for pending items
- a simple confirmation action for reviewed fallback items

**Step 4: Run test to verify it passes**

Run: `../../.venv/bin/pytest tests/test_item_confirmation_api.py tests/test_frontend_delivery.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/api/routes/items.py app/schemas/item.py app/static/index.html app/static/styles.css app/static/app.js tests/test_item_confirmation_api.py tests/test_frontend_delivery.py
git commit -m "feat: add pending item confirmation flow"
```

### Task 4: Add concrete notification provider adapters and selection

**Files:**
- Modify: `app/config.py`
- Modify: `app/services/notifier.py`
- Modify: `app/services/reminder_service.py`
- Test: `tests/test_notifier.py`
- Modify: `README.md`

**Step 1: Write the failing test**

Add tests for:
- Push Plus payload formatting
- Server酱 payload formatting
- generic webhook fallback remaining intact

**Step 2: Run test to verify it fails**

Run: `../../.venv/bin/pytest tests/test_notifier.py -v`
Expected: FAIL because the notifier only supports a generic webhook mode.

**Step 3: Write minimal implementation**

Extend notifier configuration to support provider selection:
- `generic`
- `pushplus`
- `serverchan`

Build the correct outbound payload shape for each provider while preserving the current generic webhook path.

**Step 4: Run test to verify it passes**

Run: `../../.venv/bin/pytest tests/test_notifier.py tests/test_reminders.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/config.py app/services/notifier.py app/services/reminder_service.py tests/test_notifier.py README.md
git commit -m "feat: add notification provider adapters"
```

### Task 5: Final verification and documentation refresh

**Files:**
- Modify: `README.md`
- Modify: `docs/plans/2026-04-09-project-hardening-plan.md`

**Step 1: Refresh documentation**

Document:
- the new webhook ingestion endpoint
- supported Chinese date phrases
- confirmation/edit workflow
- notification provider configuration

Completed in `README.md` with operator-facing examples for:
- `POST /api/items/voice/webhook`
- supported date phrases: `今天` / `明天` / `后天` / `N天后` / `今年10月底` / `10月31日`
- `PUT /api/items/{id}` and `POST /api/items/{id}/confirm`
- `generic`, `pushplus`, and `serverchan` notification provider setup

**Step 2: Run full verification**

Run: `../../.venv/bin/pytest -v`
Result: all tests PASS

**Step 3: Commit**

```bash
git add README.md docs/plans/2026-04-09-project-hardening-plan.md
git commit -m "docs: update hardening workflow docs"
```

Verification note:

- Full test suite completed successfully on this branch after the documentation refresh.
