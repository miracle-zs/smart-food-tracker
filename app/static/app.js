const manualForm = document.querySelector("#manual-entry-form");
const voiceForm = document.querySelector("#voice-entry-form");
const statusFilter = document.querySelector("#status-filter");
const locationFilter = document.querySelector("#location-filter");
const searchInput = document.querySelector("#inventory-search");
const sortFilter = document.querySelector("#sort-filter");
const itemsBoard = document.querySelector("#items-board");
const feedback = document.querySelector("#feedback");
const reviewPanel = document.querySelector("#edit-confirm-panel");
const pendingConfirmationList = document.querySelector("#pending-confirmation-list");
const pendingItemForm = document.querySelector("#pending-item-form");
const pendingItemIdField = pendingItemForm.querySelector('input[name="item_id"]');
const pendingItemNameField = document.querySelector("#pending-item-name");
const pendingItemLocationField = document.querySelector("#pending-item-location");
const pendingItemExpiryField = document.querySelector("#pending-item-expiry-date");
const pendingItemSaveButton = pendingItemForm.querySelector('button[type="submit"]');
const selectedItemSummary = document.querySelector("#selected-item-summary");
const confirmPendingButton = document.querySelector("#confirm-pending-item");
const summaryTotalCount = document.querySelector("#summary-total-count");
const summaryPendingCount = document.querySelector("#summary-pending-count");
const summaryDue7DaysCount = document.querySelector("#summary-due-7-days-count");
const summaryExpiredCount = document.querySelector("#summary-expired-count");
const expiredBucket = document.querySelector("#expired-items .risk-items");
const due3Bucket = document.querySelector("#due-3-days-items .risk-items");
const due7Bucket = document.querySelector("#due-7-days-items .risk-items");
const safeBucket = document.querySelector("#safe-items .risk-items");
let inventoryRequestSeq = 0;

const urgencyLabelMap = {
  expired: "已过期",
  critical: "3 天内",
  warning: "7 天内",
  safe: "安全期",
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setFeedback(message, isError = false) {
  feedback.textContent = message;
  feedback.classList.toggle("is-error", isError);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

function buildInventoryQuery() {
  const params = new URLSearchParams();
  if (statusFilter.value) {
    params.set("status", statusFilter.value);
  }
  if (locationFilter.value) {
    params.set("location", locationFilter.value);
  }
  const query = searchInput.value.trim();
  if (query) {
    params.set("q", query);
  }
  if (sortFilter.value) {
    params.set("sort", sortFilter.value);
  }
  const search = params.toString();
  return search ? `?${search}` : "";
}

function renderLocations(items) {
  if (items.length === 0) {
    return;
  }

  const currentValue = locationFilter.value;
  const options = [...new Set(items.map((item) => item.location).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, "zh-Hans-CN"),
  );

  locationFilter.innerHTML = '<option value="">全部位置</option>';
  options.forEach((location) => {
    const option = document.createElement("option");
    option.value = location;
    option.textContent = location;
    locationFilter.appendChild(option);
  });

  locationFilter.value = options.includes(currentValue) ? currentValue : "";
}

function updateSummary(summary) {
  summaryTotalCount.textContent = String(summary.total_count);
  summaryPendingCount.textContent = String(summary.pending_confirmation_count);
  summaryDue7DaysCount.textContent = String(summary.due_within_7_days_count);
  summaryExpiredCount.textContent = String(summary.expired_count);
}

function formatDayText(item) {
  return item.days_left < 0 ? `超期 ${Math.abs(item.days_left)} 天` : `剩余 ${item.days_left} 天`;
}

function badge(text, className = "") {
  return `<span class="badge${className ? ` ${className}` : ""}">${escapeHtml(text)}</span>`;
}

function encodeItemPayload(item) {
  return encodeURIComponent(
    JSON.stringify({
      id: item.id,
      name: item.name,
      location: item.location,
      expiry_date: item.expiry_date,
    }),
  );
}

function decodeItemPayload(payload) {
  return JSON.parse(decodeURIComponent(payload));
}

function renderItemCard(item, { allowStatusActions = true, allowReviewActions = true } = {}) {
  const statusActions =
    allowStatusActions && item.status === "active"
      ? `
        <button class="action-button" data-id="${item.id}" data-name="${escapeHtml(item.name)}" data-status="consumed">
          已吃完
        </button>
        <button class="action-button" data-id="${item.id}" data-name="${escapeHtml(item.name)}" data-status="discarded">
          已丢弃
        </button>
      `
      : "";
  const reviewActions =
    allowReviewActions && item.status === "active" && item.needs_confirmation
      ? `
        <button class="action-button" data-action="open-editor" data-item="${encodeItemPayload(item)}">
          编辑
        </button>
        <button class="action-button" data-action="confirm-item" data-item="${encodeItemPayload(item)}" data-id="${item.id}" data-name="${escapeHtml(item.name)}">
          确认
        </button>
      `
      : "";
  const pendingBadge = item.needs_confirmation ? badge("待确认", "badge-outline") : "";

  return `
    <article class="item-card" data-item-id="${item.id}">
      <div>
        <p class="item-title">${escapeHtml(item.name)}</p>
        <p class="item-meta">${escapeHtml(item.location)}</p>
      </div>
      <div class="item-expiry">
        <div>${escapeHtml(item.expiry_date)}</div>
        <div>${escapeHtml(formatDayText(item))}</div>
      </div>
      <div class="badge-row">
        ${badge(urgencyLabelMap[item.urgency] || item.urgency, `badge-${item.urgency}`)}
        ${badge(item.status, "badge-outline")}
        ${pendingBadge}
      </div>
      <div class="item-actions">
        ${statusActions}
        ${reviewActions}
      </div>
    </article>
  `;
}

function renderInventory(items) {
  if (items.length === 0) {
    itemsBoard.innerHTML = '<div class="empty-state">当前筛选条件下没有条目。</div>';
    return;
  }

  itemsBoard.innerHTML = items.map((item) => renderItemCard(item)).join("");
}

function renderRiskBucket(container, items, emptyText) {
  if (!container) {
    return;
  }

  if (items.length === 0) {
    container.innerHTML = `<div class="empty-state">${escapeHtml(emptyText)}</div>`;
    return;
  }

  container.innerHTML = items.map((item) => renderItemCard(item)).join("");
}

function renderRiskBoard(items) {
  const activeItems = items.filter((item) => item.status === "active");
  renderRiskBucket(
    expiredBucket,
    activeItems.filter((item) => item.urgency === "expired"),
    "暂无已过期条目。",
  );
  renderRiskBucket(
    due3Bucket,
    activeItems.filter((item) => item.urgency === "critical"),
    "暂无 3 天内到期条目。",
  );
  renderRiskBucket(
    due7Bucket,
    activeItems.filter((item) => item.urgency === "warning"),
    "暂无 7 天内到期条目。",
  );
  renderRiskBucket(
    safeBucket,
    activeItems.filter((item) => item.urgency === "safe"),
    "暂无安全期条目。",
  );
}

function renderPendingQueue(items) {
  const pendingItems = items.filter((item) => item.status === "active" && item.needs_confirmation);

  if (pendingItems.length === 0) {
    pendingConfirmationList.innerHTML = '<li class="empty-state">暂无待确认条目。</li>';
    return;
  }

  pendingConfirmationList.innerHTML = pendingItems
    .map(
      (item) => `
        <li class="pending-queue-item" data-item-id="${item.id}">
          ${renderItemCard(item, { allowStatusActions: false, allowReviewActions: true })}
        </li>
      `,
    )
    .join("");
}

async function loadSummary() {
  try {
    const summary = await requestJson("/api/items/summary", { method: "GET" });
    updateSummary(summary);
  } catch (error) {
    setFeedback("概览加载失败，请检查后端服务。", true);
  }
}

async function loadActiveDashboardItems() {
  try {
    const items = await requestJson("/api/items?status=active&sort=expiry_date_asc", {
      method: "GET",
    });
    renderRiskBoard(items);
    renderPendingQueue(items);
  } catch (error) {
    setFeedback("风险看板加载失败，请稍后重试。", true);
  }
}

async function loadInventoryItems() {
  const requestSeq = ++inventoryRequestSeq;
  try {
    const items = await requestJson(`/api/items${buildInventoryQuery()}`, {
      method: "GET",
    });
    if (requestSeq !== inventoryRequestSeq) {
      return;
    }
    renderLocations(items);
    renderInventory(items);
  } catch (error) {
    if (requestSeq !== inventoryRequestSeq) {
      return;
    }
    setFeedback("库存列表加载失败，请稍后重试。", true);
  }
}

async function refreshDashboard() {
  await Promise.all([loadSummary(), loadActiveDashboardItems(), loadInventoryItems()]);
}

function openReviewPanel(item) {
  pendingItemIdField.value = String(item.id);
  pendingItemNameField.disabled = false;
  pendingItemLocationField.disabled = false;
  pendingItemExpiryField.disabled = false;
  pendingItemSaveButton.disabled = false;
  pendingItemNameField.value = item.name;
  pendingItemLocationField.value = item.location;
  pendingItemExpiryField.value = item.expiry_date;
  selectedItemSummary.textContent = `正在编辑 ${item.name}，位置 ${item.location}，到期 ${item.expiry_date}。`;
  confirmPendingButton.disabled = false;
  reviewPanel.classList.add("is-active");
}

function resetReviewPanel() {
  pendingItemForm.reset();
  pendingItemIdField.value = "";
  pendingItemNameField.disabled = true;
  pendingItemLocationField.disabled = true;
  pendingItemExpiryField.disabled = true;
  pendingItemSaveButton.disabled = true;
  confirmPendingButton.disabled = true;
  selectedItemSummary.textContent = "选择一个待确认条目后，可以在这里修正名称、位置和过期日期。";
  reviewPanel.classList.remove("is-active");
}

async function confirmItem(item) {
  await requestJson(`/api/items/${item.id}/confirm`, {
    method: "POST",
  });
  resetReviewPanel();
  setFeedback(`已确认 ${item.name}，待确认标记已清除。`);
  await refreshDashboard();
}

async function handlePendingItemSubmit(event) {
  event.preventDefault();
  const itemId = pendingItemIdField.value;
  if (!itemId) {
    setFeedback("请先在待确认列表中选择一个条目，再保存修改。", true);
    return;
  }

  const formData = new FormData(pendingItemForm);
  const payload = Object.fromEntries(formData.entries());
  delete payload.item_id;

  try {
    await requestJson(`/api/items/${itemId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    resetReviewPanel();
    setFeedback(`已保存 ${payload.name} 的待确认修改。`);
    await refreshDashboard();
  } catch (error) {
    setFeedback("保存待确认修改失败，请稍后重试。", true);
  }
}

async function handleManualSubmit(event) {
  event.preventDefault();
  const formData = new FormData(manualForm);
  const payload = Object.fromEntries(formData.entries());

  try {
    await requestJson("/api/items", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    manualForm.reset();
    setFeedback(`手动录入成功：${payload.name} 已加入库存。`);
    await refreshDashboard();
  } catch (error) {
    setFeedback("手动录入失败，请检查名称、位置和日期后重试。", true);
  }
}

async function handleVoiceSubmit(event) {
  event.preventDefault();
  const formData = new FormData(voiceForm);
  const payload = Object.fromEntries(formData.entries());

  try {
    const response = await requestJson("/api/items/voice", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    voiceForm.reset();
    const confirmationText = response.item.needs_confirmation ? "，已进入待确认队列。" : "，已直接入库。";
    setFeedback(`语音录入成功：${response.item.name}${confirmationText}`);
    await refreshDashboard();
  } catch (error) {
    setFeedback("语音录入失败，请检查转写内容后重试。", true);
  }
}

async function handleDashboardAction(event) {
  const button = event.target.closest("button");
  if (!button) {
    return;
  }

  if (button.dataset.action === "open-editor") {
    openReviewPanel(decodeItemPayload(button.dataset.item));
    setFeedback("已打开待确认条目的编辑面板。");
    return;
  }

  if (button.dataset.action === "confirm-item") {
    try {
      await confirmItem(decodeItemPayload(button.dataset.item));
    } catch (error) {
      setFeedback("确认待确认条目失败，请稍后重试。", true);
    }
    return;
  }

  if (button.dataset.status) {
    const itemName = button.dataset.name || "条目";
    try {
      await requestJson(`/api/items/${button.dataset.id}/status`, {
        method: "PUT",
        body: JSON.stringify({ status: button.dataset.status }),
      });
      if (pendingItemIdField.value === String(button.dataset.id)) {
        resetReviewPanel();
      }
      const statusText = button.dataset.status === "consumed" ? "已吃完" : "已丢弃";
      setFeedback(`${itemName} 状态已更新为 ${statusText}。`);
      await refreshDashboard();
    } catch (error) {
      setFeedback("更新条目状态失败，请稍后重试。", true);
    }
  }
}

manualForm.addEventListener("submit", handleManualSubmit);
voiceForm.addEventListener("submit", handleVoiceSubmit);
pendingItemForm.addEventListener("submit", handlePendingItemSubmit);
confirmPendingButton.addEventListener("click", async () => {
  const itemId = pendingItemIdField.value;
  if (!itemId) {
    setFeedback("请先在待确认列表中选择一个条目，再确认。", true);
    return;
  }

  const item = {
    id: Number(itemId),
    name: pendingItemNameField.value || "待确认条目",
    location: pendingItemLocationField.value,
    expiry_date: pendingItemExpiryField.value,
  };

  try {
    await confirmItem(item);
  } catch (error) {
    setFeedback("确认待确认条目失败，请稍后重试。", true);
  }
});
statusFilter.addEventListener("change", loadInventoryItems);
locationFilter.addEventListener("change", loadInventoryItems);
searchInput.addEventListener("input", loadInventoryItems);
sortFilter.addEventListener("change", loadInventoryItems);
itemsBoard.addEventListener("click", handleDashboardAction);
document.querySelector("#risk-board-section").addEventListener("click", handleDashboardAction);
pendingConfirmationList.addEventListener("click", handleDashboardAction);

resetReviewPanel();
refreshDashboard();
