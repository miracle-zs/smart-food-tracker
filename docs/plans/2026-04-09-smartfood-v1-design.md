# SmartFood Tracker V1 Design

## Goal

Upgrade the current MVP into a household-ready V1 product that helps families monitor expiry risk, resolve uncertain voice-ingested items, and manage home food inventory from a clearer, more productized dashboard.

## Product Scope

This V1 targets single-household self-use only.

Included:

- dashboard overview with inventory health summary
- grouped risk board for active items
- dedicated pending-confirmation workflow
- manual and voice-based item intake
- searchable and filterable inventory management
- mobile-friendly responsive UI

Explicitly excluded:

- login and registration
- multi-household support
- family member collaboration
- image recognition intake
- advanced notification preference center
- commercialization or billing concerns

## Product Positioning

The MVP behaves like a useful internal tool. V1 should behave like a household food manager.

The homepage should no longer center on input forms. It should center on:

1. what needs attention today
2. what still needs confirmation
3. how to quickly add new items
4. how to inspect the full household inventory

## Information Architecture

### 1. Summary Section

The first screen presents the current household inventory status through compact summary cards:

- total items
- expired items
- items expiring within 3 days
- items expiring within 7 days
- pending confirmation items
- location coverage count

The purpose is to let the user understand inventory health in a few seconds.

### 2. Risk Priority Section

Active items are grouped into four priority buckets:

- expired
- within 3 days
- within 7 days
- safe

The first two groups receive stronger visual emphasis. Each item card supports direct status actions so users can complete routine handling without navigating away.

### 3. Pending Confirmation Section

Items created from uncertain voice parsing should not be mixed into the normal board experience. They belong in a dedicated review workflow where the user can:

- inspect the parsed result
- correct name, location, and expiry date
- save edits
- confirm the item and remove the pending marker

This section reduces ambiguity and keeps the main inventory view trustworthy.

### 4. Quick Intake Section

Manual entry and voice-text entry remain important, but they should be presented as quick-add actions rather than the central purpose of the page.

The system should clearly communicate after intake:

- whether the item was created successfully
- which risk group it falls into
- whether it needs confirmation

### 5. Full Inventory Section

The bottom section serves as the household ledger. It must support:

- free-text search by item name or location
- status filter
- location filter
- sorting controls

This section supports retrieval and management when the user wants to inspect all records instead of only urgent ones.

## Core User Flows

### Daily Check

The user opens the dashboard and immediately sees summary metrics and high-risk items. The interface should make it obvious which items need action first.

### Fast Handling

The user marks an item as consumed or discarded directly from the risk card. The summary, grouped risk view, and inventory list refresh immediately.

### Pending Review

The user opens a pending item, edits structured fields, saves changes, and confirms it. After confirmation, the item leaves the pending workflow and appears as a normal active inventory item.

### Item Intake

The user adds an item manually or through a voice transcript. The system returns a result that is easy to understand and does not require reading raw API details.

## Backend Design

The current FastAPI + SQLite + SQLAlchemy structure is sufficient for V1 and should remain intact.

### New API Capability

Add `GET /api/items/summary` to expose aggregate counts for the dashboard:

- total items
- pending confirmation items
- expired items
- items due within 3 days
- items due within 7 days
- distinct active location count
- per-location counts for active items

### Extended List API

Extend `GET /api/items` with:

- `q` for free-text search over item name and location
- `sort` for explicit ordering

Suggested supported sort modes:

- `expiry_date_asc`
- `expiry_date_desc`
- `entry_date_desc`

Default sort remains expiry ascending.

### Existing Endpoints

Keep these endpoints stable:

- `POST /api/items`
- `POST /api/items/voice`
- `POST /api/items/voice/webhook`
- `PUT /api/items/{id}`
- `POST /api/items/{id}/confirm`
- `PUT /api/items/{id}/status`

## Frontend Design

The static frontend remains the delivery mechanism, but the page should be restructured into a product dashboard rather than a utility board.

Key frontend changes:

- summary cards with dynamic metrics
- grouped risk board with section headers and empty states
- dedicated pending list and edit workflow
- improved search and sort controls
- stronger feedback messaging
- mobile-first responsive fallback for all main actions

The visual tone should feel intentional and productized while remaining practical for kitchen use.

## UX Rules

- Users should understand the current inventory state within 3 seconds.
- High-risk items must be easier to act on than safe items.
- Pending confirmation must have a clearly separated workflow.
- Empty states must guide the next action instead of simply saying there is no data.
- Success and failure feedback must always explain the result in plain language.

## Testing Strategy

V1 should add or extend automated tests for:

- summary endpoint aggregation
- search behavior on item name and location
- supported sort modes
- status changes coexisting with search and filters
- dashboard shell delivery of new product sections

Manual verification should cover:

- mobile viewport layout
- pending item edit and confirm workflow
- feedback messages after create, update, confirm, and status-change actions

## Acceptance Criteria

- The homepage reads like a product homepage, not a development panel.
- Users can identify urgent food items without manually filtering.
- Pending items have an explicit review workflow.
- Inventory can be searched and filtered efficiently.
- The main experience is usable on mobile.
- Core flows are covered by automated tests.
