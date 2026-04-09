from html.parser import HTMLParser


class ElementCaptureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def _parse_elements(html):
    parser = ElementCaptureParser()
    parser.feed(html)
    return parser.elements


def test_dashboard_shell_serves_forms_and_item_board(client):
    response = client.get("/")

    assert response.status_code == 200
    elements = _parse_elements(response.text)

    section_ids = {
        attrs.get("id")
        for tag, attrs in elements
        if tag == "section"
    }
    assert {
        "summary-section",
        "risk-board-section",
        "edit-confirm-panel",
        "quick-intake-section",
        "inventory-section",
    }.issubset(section_ids)

    strong_ids = {
        attrs.get("id")
        for tag, attrs in elements
        if tag == "strong"
    }
    assert {
        "summary-total-count",
        "summary-pending-count",
        "summary-due-7-days-count",
        "summary-expired-count",
    }.issubset(strong_ids)

    assert any(tag == "form" and attrs.get("id") == "manual-entry-form" for tag, attrs in elements)
    assert any(tag == "form" and attrs.get("id") == "voice-entry-form" for tag, attrs in elements)
    assert any(tag == "form" and attrs.get("id") == "pending-item-form" for tag, attrs in elements)
    assert any(tag == "button" and attrs.get("id") == "confirm-pending-item" for tag, attrs in elements)
    assert any(tag == "div" and attrs.get("id") == "items-board" for tag, attrs in elements)
    assert any(tag == "script" and attrs.get("src") == "/static/app.js" for tag, attrs in elements)


def test_dashboard_script_resets_review_panel_after_save_and_confirm(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    script = response.text
    assert "function resetReviewPanel()" in script
    assert "pendingItemIdField.value = \"\";" in script
    assert "pendingItemNameField.disabled = true;" in script
    assert "confirmPendingButton.disabled = true;" in script
    assert "resetReviewPanel();" in script


def test_dashboard_script_exposes_v1_loading_and_interaction_hooks(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    script = response.text

    expected_fragments = [
        'requestJson("/api/items/summary"',
        "let inventoryRequestSeq = 0;",
        "const requestSeq = ++inventoryRequestSeq;",
        "if (requestSeq !== inventoryRequestSeq) {",
        'if (items.length === 0) {',
        'document.querySelector("#summary-total-count")',
        'document.querySelector("#inventory-search")',
        'document.querySelector("#sort-filter")',
        'document.querySelector("#expired-items .risk-items")',
        'document.querySelector("#due-3-days-items .risk-items")',
        'document.querySelector("#due-7-days-items .risk-items")',
        'document.querySelector("#safe-items .risk-items")',
        'document.querySelector("#pending-item-form")',
        'document.querySelector("#confirm-pending-item")',
        'document.querySelector("#pending-confirmation-list")',
        'button.dataset.action === "open-editor"',
        'openReviewPanel(decodeItemPayload(button.dataset.item))',
        'pendingConfirmationList.addEventListener("click", handleDashboardAction)',
    ]

    for fragment in expected_fragments:
        assert fragment in script
