# SmartFood Frontend Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the SmartFood Tracker frontend into a premium "precision appliance" dashboard while preserving the existing V1 functionality and backend contract.

**Architecture:** Keep the existing static HTML/CSS/JS delivery model. Refine the HTML shell where needed to support a more explicit visual hierarchy, then rework the stylesheet into a stronger design system and apply only minimal JavaScript hook changes if the redesigned presentation needs additional semantic classes or state markers.

**Tech Stack:** HTML, CSS, JavaScript, FastAPI static delivery, pytest

---

### Task 1: Refine the HTML shell for the new visual contract

**Files:**
- Modify: `app/static/index.html`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

Extend `tests/test_frontend_delivery.py` so it asserts any new stable shell hooks required by the redesign. Keep the test delivery-level and structural.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_delivery.py::test_dashboard_shell_serves_forms_and_item_board -v`
Expected: FAIL because the new shell markers for the redesign do not exist yet.

**Step 3: Write minimal implementation**

Update `app/static/index.html` to support the new precision-appliance visual hierarchy:

- refine hero structure into a top control rail
- add any stable wrapper classes needed for instrument-style summary cards
- add any stable wrapper classes needed for chamber-style risk groups
- add any stable wrapper classes needed for the pending workbench and inventory command strip

Preserve all current IDs used by JavaScript unless there is a documented replacement.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_delivery.py::test_dashboard_shell_serves_forms_and_item_board -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/static/index.html tests/test_frontend_delivery.py
git commit -m "feat: refine frontend shell for precision redesign"
```

### Task 2: Rebuild the stylesheet into the precision-appliance design system

**Files:**
- Modify: `app/static/styles.css`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

Extend `tests/test_frontend_delivery.py` to assert the stylesheet exposes any new stable contract fragments required by the redesign:

- top control rail styling hook
- instrument summary styling hook
- chamber or risk module styling hook
- pending workbench styling hook
- responsive breakpoints still present

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_delivery.py::test_dashboard_stylesheet_exposes_v1_layout_and_responsive_rules -v`
Expected: FAIL because the new style contract is not present yet.

**Step 3: Write minimal implementation**

Rewrite `app/static/styles.css` to match the approved direction:

- stronger precision-material palette
- more instrument-like summary cards
- more chamber-like risk groups
- more operational pending workbench styling
- stricter command-strip treatment for filters
- mobile-safe layout transitions

Keep selectors explicit and avoid brittle child-order dependencies.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_delivery.py::test_dashboard_stylesheet_exposes_v1_layout_and_responsive_rules -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/static/styles.css tests/test_frontend_delivery.py
git commit -m "feat: apply precision frontend design system"
```

### Task 3: Add any minimal JavaScript presentation hooks required by the redesign

**Files:**
- Modify: `app/static/app.js`
- Test: `tests/test_frontend_delivery.py`

**Step 1: Write the failing test**

If the redesign requires new semantic classes, state hooks, or container-specific markup emitted by JavaScript, extend `tests/test_frontend_delivery.py` with source-level assertions for those hooks.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_delivery.py::test_dashboard_script_exposes_v1_loading_and_interaction_hooks -v`
Expected: FAIL if the new presentation hooks are not emitted yet.

**Step 3: Write minimal implementation**

Update `app/static/app.js` only as needed to support the redesigned presentation:

- add minimal class hooks for rendered risk cards or queue cards
- preserve all current behaviors
- avoid logic rewrites unless a presentation bug forces a small correction

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_delivery.py::test_dashboard_script_exposes_v1_loading_and_interaction_hooks -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/static/app.js tests/test_frontend_delivery.py
git commit -m "feat: add redesign presentation hooks"
```

### Task 4: Full frontend verification

**Files:**
- Modify: `README.md` if a short visual-description update is warranted

**Step 1: Run focused verification**

Run: `pytest tests/test_frontend_delivery.py -v`
Expected: PASS

Run: `node --check app/static/app.js`
Expected: exit 0

**Step 2: Run regression verification**

Run: `pytest -v`
Expected: all tests PASS

**Step 3: Run app smoke check**

Run: `uvicorn app.main:app --port 8010`
Expected: server starts cleanly

Then verify:

- `curl -s http://127.0.0.1:8010/health`
  Expected: `{"status":"ok"}`
- `curl -s http://127.0.0.1:8010/`
  Expected: rebuilt dashboard HTML

**Step 4: Commit**

```bash
git add app/static/index.html app/static/styles.css app/static/app.js tests/test_frontend_delivery.py README.md
git commit -m "feat: redesign smartfood frontend"
```
