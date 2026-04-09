const manualForm = document.querySelector("#manual-entry-form");
const voiceForm = document.querySelector("#voice-entry-form");
const statusFilter = document.querySelector("#status-filter");
const locationFilter = document.querySelector("#location-filter");
const itemsBoard = document.querySelector("#items-board");
const feedback = document.querySelector("#feedback");
const reviewPanel = document.querySelector("#edit-confirm-panel");
const pendingItemForm = document.querySelector("#pending-item-form");
const pendingItemIdField = pendingItemForm.querySelector('input[name="item_id"]');
const pendingItemNameField = document.querySelector("#pending-item-name");
const pendingItemLocationField = document.querySelector("#pending-item-location");
const pendingItemExpiryField = document.querySelector("#pending-item-expiry-date");
const pendingItemSaveButton = pendingItemForm.querySelector('button[type="submit"]');
const selectedItemSummary = document.querySelector("#selected-item-summary");
const confirmPendingButton = document.querySelector("#confirm-pending-item");

const urgencyLabelMap = {
  expired: "已过期",
  critical: "3 天内",
  warning: "7 天内",
  safe: "安全期",
};

function setFeedback(message, isError = false) {
  feedback.textContent = message;
  feedback.classList.toggle("is-error", isError);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

function buildQuery() {
  const params = new URLSearchParams();
  if (statusFilter.value) {
    params.set("status", statusFilter.value);
  }
  if (locationFilter.value) {
    params.set("location", locationFilter.value);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

function renderLocations(items) {
  const currentValue = locationFilter.value;
  const options = [...new Set(items.map((item) => item.location).filter(Boolean))];
  locationFilter.innerHTML = '<option value="">全部位置</option>';
  options.forEach((location) => {
    const option = document.createElement("option");
    option.value = location;
    option.textContent = location;
    locationFilter.appendChild(option);
  });
  locationFilter.value = options.includes(currentValue) ? currentValue : "";
}

function createBadge(text, className) {
  return `<span class="badge ${className}">${text}</span>`;
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

function itemCardTemplate(item) {
  const dayText = item.days_left < 0 ? `超期 ${Math.abs(item.days_left)} 天` : `剩余 ${item.days_left} 天`;
  const pendingBadge = item.needs_confirmation
    ? createBadge("待确认", "badge badge-outline")
    : "";
  const pendingActions =
    item.needs_confirmation && item.status === "active"
      ? `
        <button class="action-button" data-action="open-editor" data-item="${encodeItemPayload(item)}">
          编辑
        </button>
        <button class="action-button" data-action="confirm-item" data-id="${item.id}">
          确认
        </button>
      `
      : "";

  return `
    <article class="item-card">
      <div>
        <p class="item-title">${item.name}</p>
        <p class="item-meta">${item.location}</p>
      </div>
      <div class="item-expiry">
        <div>${item.expiry_date}</div>
        <div>${dayText}</div>
      </div>
      <div class="badge-row">
        ${createBadge(urgencyLabelMap[item.urgency] || item.urgency, `badge-${item.urgency}`)}
        ${createBadge(item.status, "badge-outline")}
        ${pendingBadge}
      </div>
      <div class="item-actions">
        ${item.status === "active" ? `<button class="action-button" data-id="${item.id}" data-status="consumed">已吃完</button>` : ""}
        ${item.status === "active" ? `<button class="action-button" data-id="${item.id}" data-status="discarded">已丢弃</button>` : ""}
        ${pendingActions}
      </div>
    </article>
  `;
}

function renderItems(items) {
  if (items.length === 0) {
    itemsBoard.innerHTML = '<div class="empty-state">当前筛选条件下没有条目。</div>';
    return;
  }
  itemsBoard.innerHTML = items.map(itemCardTemplate).join("");
}

async function loadItems() {
  try {
    const items = await requestJson(`/api/items${buildQuery()}`, { method: "GET" });
    renderLocations(items);
    renderItems(items);
    setFeedback(`已加载 ${items.length} 条记录`);
  } catch (error) {
    setFeedback("加载条目失败，请检查后端服务。", true);
  }
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

async function confirmItem(itemId) {
  await requestJson(`/api/items/${itemId}/confirm`, {
    method: "POST",
  });
  resetReviewPanel();
  setFeedback("待确认标记已清除");
  await loadItems();
}

async function handlePendingItemSubmit(event) {
  event.preventDefault();
  const itemId = pendingItemIdField.value;
  if (!itemId) {
    setFeedback("请先从看板选择一个待确认条目。", true);
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
    setFeedback("条目已更新");
    await loadItems();
  } catch (error) {
    setFeedback("条目更新失败，请稍后重试。", true);
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
    setFeedback("手动录入成功");
    await loadItems();
  } catch (error) {
    setFeedback("手动录入失败，请检查输入格式。", true);
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
    const confirmationText = response.item.needs_confirmation ? "，已标记待确认" : "";
    setFeedback(`语音录入成功：${response.item.name}${confirmationText}`);
    await loadItems();
  } catch (error) {
    setFeedback("语音录入失败，请稍后重试。", true);
  }
}

async function handleBoardAction(event) {
  const button = event.target.closest("button[data-id], button[data-action]");
  if (!button) {
    return;
  }

  try {
    if (button.dataset.action === "open-editor") {
      openReviewPanel(JSON.parse(decodeURIComponent(button.dataset.item)));
      setFeedback("已打开待确认条目的编辑面板");
      return;
    }

    if (button.dataset.action === "confirm-item") {
      await confirmItem(button.dataset.id);
      return;
    }

    if (button.dataset.status) {
      await requestJson(`/api/items/${button.dataset.id}/status`, {
        method: "PUT",
        body: JSON.stringify({ status: button.dataset.status }),
      });
      setFeedback("状态已更新");
      await loadItems();
    }
  } catch (error) {
    if (button.dataset.action === "confirm-item") {
      setFeedback("确认失败。", true);
      return;
    }
    if (button.dataset.action === "open-editor") {
      setFeedback("无法打开编辑面板。", true);
      return;
    }
    setFeedback("状态更新失败。", true);
  }
}

manualForm.addEventListener("submit", handleManualSubmit);
voiceForm.addEventListener("submit", handleVoiceSubmit);
pendingItemForm.addEventListener("submit", handlePendingItemSubmit);
confirmPendingButton.addEventListener("click", async () => {
  const itemId = pendingItemIdField.value;
  if (!itemId) {
    setFeedback("请先从看板选择一个待确认条目。", true);
    return;
  }

  try {
    await confirmItem(itemId);
  } catch (error) {
    setFeedback("确认失败。", true);
  }
});
statusFilter.addEventListener("change", loadItems);
locationFilter.addEventListener("change", loadItems);
itemsBoard.addEventListener("click", handleBoardAction);

loadItems();
