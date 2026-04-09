# SmartFood Tracker V1 Productization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade SmartFood Tracker from MVP to a household-ready V1 by adding dashboard summary data, search and sort support, a risk-grouped homepage, a dedicated pending-confirmation workflow, and a more productized responsive frontend.

**Architecture:** Keep the current single-app FastAPI architecture. Extend the existing item routes with aggregate and query features, then rebuild the static dashboard to consume those APIs and present the inventory as a guided household product experience rather than a flat utility page.

**Tech Stack:** Python, FastAPI, SQLAlchemy, pytest, HTML, CSS, JavaScript

---

### Task 1: Add summary API schema and aggregation endpoint

**Files:**
- Modify: `app/schemas/item.py`
- Modify: `app/api/routes/items.py`
- Test: `tests/test_item_summary_api.py`

**Step 1: Write the failing test**

Create `tests/test_item_summary_api.py` covering:

- total item count across all statuses
- pending confirmation count
- expired count
- due within 3 days count
- due within 7 days count
- distinct location count for active items
- per-location counts for active items

Use fixed expiry dates relative to `date.today()` so the assertions match the route logic.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_item_summary_api.py -v`
Expected: FAIL because the summary schema and route do not exist.

**Step 3: Write minimal implementation**

Add response models in `app/schemas/item.py` for summary payloads.

Add `GET /api/items/summary` in `app/api/routes/items.py` that:

- queries `FoodItem`
- computes counts using the same date semantics as `to_item_response`
- limits location statistics to active items
- returns a deterministic structure suitable for dashboard rendering

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_item_summary_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/schemas/item.py app/api/routes/items.py tests/test_item_summary_api.py
git commit -m "feat: add dashboard summary API"
```

### Task 2: Extend item list querying with search and sort

**Files:**
- Modify: `app/api/routes/items.py`
- Modify: `app/schemas/item.py`
- Test: `tests/test_item_querying.py`

**Step 1: Write the failing test**

Create `tests/test_item_querying.py` covering:

- `q` matches item name
- `q` matches location
- search still respects `status`
- search still respects `location`
- `sort=expiry_date_asc`
- `sort=expiry_date_desc`
- `sort=entry_date_desc`
- invalid sort falls back to default expiry ascending behavior

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_item_querying.py -v`
Expected: FAIL because free-text search and explicit sort are not implemented.

**Step 3: Write minimal implementation**

Extend `GET /api/items` in `app/api/routes/items.py` to accept:

- `q: str | None`
- `sort: str | None`

Implement case-insensitive partial matching against `FoodItem.name` and `FoodItem.location`.

Implement explicit ordering rules while preserving existing behavior for callers that omit `sort`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_item_querying.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/api/routes/items.py app/schemas/item.py tests/test_item_querying.py
git commit -m "feat: add inventory search and sort"
```

### Task 3: Rebuild the dashboard shell for V1 product structure

**Files:**
- Modify: `app/static/index.html`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

Extend `tests/test_frontend_delivery.py` to assert the root page includes identifiable V1 sections, for example:

- summary section
- risk board section
- pending confirmation section
- quick intake section
- full inventory section

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: FAIL because the current HTML shell does not expose the new product sections.

**Step 3: Write minimal implementation**

Restructure `app/static/index.html` to include:

- top summary area with metric placeholders
- risk-group containers for expired, 3-day, 7-day, and safe items
- dedicated pending-confirmation list plus edit form
- quick intake area for manual and voice entry
- full inventory area with search, filters, and sort controls

Preserve existing script and stylesheet loading.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/static/index.html tests/test_frontend_delivery.py
git commit -m "feat: restructure dashboard for V1"
```

### Task 4: Implement dashboard data loading and interaction logic

**Files:**
- Modify: `app/static/app.js`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

Extend `tests/test_frontend_delivery.py` to verify the frontend asset is still referenced and contains hooks for:

- summary loading
- search form
- sort control
- risk buckets
- pending review interactions

Keep this as a delivery-level test rather than a browser automation suite.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: FAIL because the current script is centered on a flat board and lacks the new hooks.

**Step 3: Write minimal implementation**

Refactor `app/static/app.js` to:

- fetch `/api/items/summary`
- fetch `/api/items` with `status`, `location`, `q`, and `sort`
- render grouped active items into separate risk buckets
- render pending items into a dedicated queue
- keep the edit-and-confirm flow bound to pending items
- update summary cards after all mutating actions
- preserve status updates for active items
- provide clearer success and failure messages

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/static/app.js tests/test_frontend_delivery.py
git commit -m "feat: add V1 dashboard interactions"
```

### Task 5: Productize the visual system and responsive layout

**Files:**
- Modify: `app/static/styles.css`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

If needed, extend `tests/test_frontend_delivery.py` with stable selectors or section classes that ensure the new layout structure exists and the stylesheet is still served.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: FAIL if the new product sections or selectors are not reflected in the delivered page.

**Step 3: Write minimal implementation**

Update `app/static/styles.css` to support:

- polished summary cards
- grouped risk sections
- stronger hierarchy between urgent and safe content
- pending review work area
- inventory controls
- mobile-friendly stacking and spacing

Keep the styling consistent with the current project tone while making the page feel like a production dashboard.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/static/styles.css tests/test_frontend_delivery.py
git commit -m "feat: refine V1 dashboard styling"
```

### Task 6: Update documentation and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/plans/2026-04-09-smartfood-v1-design.md`
- Modify: `docs/plans/2026-04-09-smartfood-v1-implementation.md`

**Step 1: Update documentation**

Refresh `README.md` to describe the V1 dashboard experience and newly available query capabilities:

- summary endpoint
- search and sort parameters
- productized homepage sections

Only update the plan documents if implementation reveals a necessary correction.

**Step 2: Run focused verification**

Run: `pytest tests/test_item_summary_api.py tests/test_item_querying.py tests/test_frontend_delivery.py -v`
Expected: PASS

**Step 3: Run regression verification**

Run: `pytest -v`
Expected: all tests PASS

**Step 4: Run app smoke check**

Run: `uvicorn app.main:app --reload`
Expected: app starts cleanly and serves `/`, `/health`, `/docs`, and the rebuilt dashboard

**Step 5: Commit**

```bash
git add README.md docs/plans/2026-04-09-smartfood-v1-design.md docs/plans/2026-04-09-smartfood-v1-implementation.md app tests
git commit -m "docs: add smartfood V1 productization plan"
```
