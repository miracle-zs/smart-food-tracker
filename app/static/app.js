const manualForm = document.querySelector("#manual-entry-form");
const voiceForm = document.querySelector("#voice-entry-form");
const statusFilter = document.querySelector("#status-filter");
const locationFilter = document.querySelector("#location-filter");
const itemsBoard = document.querySelector("#items-board");
const feedback = document.querySelector("#feedback");

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

function itemCardTemplate(item) {
  const dayText = item.days_left < 0 ? `超期 ${Math.abs(item.days_left)} 天` : `剩余 ${item.days_left} 天`;
  const pendingBadge = item.needs_confirmation
    ? createBadge("待确认", "badge badge-outline")
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
  const button = event.target.closest("button[data-id][data-status]");
  if (!button) {
    return;
  }

  try {
    await requestJson(`/api/items/${button.dataset.id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: button.dataset.status }),
    });
    setFeedback("状态已更新");
    await loadItems();
  } catch (error) {
    setFeedback("状态更新失败。", true);
  }
}

manualForm.addEventListener("submit", handleManualSubmit);
voiceForm.addEventListener("submit", handleVoiceSubmit);
statusFilter.addEventListener("change", loadItems);
locationFilter.addEventListener("change", loadItems);
itemsBoard.addEventListener("click", handleBoardAction);

loadItems();
