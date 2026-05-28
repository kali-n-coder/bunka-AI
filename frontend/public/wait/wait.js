const REFRESH_MS = 30000;

const elements = {
  list: document.querySelector("#waitList"),
  empty: document.querySelector("#emptyMessage"),
  search: document.querySelector("#searchInput"),
  category: document.querySelector("#categorySelect"),
  connection: document.querySelector("#connectionLabel"),
  updated: document.querySelector("#updatedLabel"),
  count: document.querySelector("#countValue"),
  quiet: document.querySelector("#quietValue"),
  max: document.querySelector("#maxValue"),
};

let allItems = [];
let config = null;

function waitTone(minutes) {
  if (minutes <= 5) return "quiet";
  if (minutes <= 20) return "normal";
  if (minutes <= 45) return "busy";
  return "full";
}

function waitLabel(minutes) {
  if (minutes <= 5) return "空いている";
  if (minutes <= 20) return "やや混雑";
  if (minutes <= 45) return "混雑";
  return "かなり混雑";
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return map[char];
  });
}

async function loadJson(path) {
  const response = await fetch(`${path}?t=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} を読み込めませんでした`);
  return response.json();
}

async function loadConfig() {
  try {
    config = await loadJson("./firebase_config.json");
  } catch {
    config = { mode: "sample", samplePath: "./wait_times.sample.json" };
  }
}

function firebaseUrl() {
  const databaseUrl = String(config.databaseUrl || "").replace(/\/$/, "");
  const path = String(config.path || "publicWaitTimes").replace(/^\/|\/$/g, "");
  if (!databaseUrl) return "";
  return `${databaseUrl}/${path}.json`;
}

async function fetchWaitTimes() {
  if (!config) await loadConfig();

  const mode = config.mode || "firebase-rtdb";
  if (mode === "sample") {
    elements.connection.textContent = "サンプル表示";
    return loadJson(config.samplePath || "./wait_times.sample.json");
  }

  const url = firebaseUrl();
  if (!url) throw new Error("FirebaseのdatabaseUrlが未設定です");
  const data = await loadJson(url);
  elements.connection.textContent = "最新データ";
  return data;
}

function normalizeItems(data) {
  const rawItems = Array.isArray(data) ? data : Object.values(data || {});
  return rawItems
    .filter((item) => item && typeof item === "object")
    .map((item, index) => ({
      id: Number(item.id ?? index + 1),
      exhibition_id: Number(item.exhibition_id ?? item.id ?? index + 1),
      exhibition_name: item.exhibition_name || item.name || `企画 ${index + 1}`,
      category: item.category || "未分類",
      location_name: item.location_name || "場所未設定",
      duration_minutes: Number(item.duration_minutes || 0),
      current_wait_minutes: Number(item.current_wait_minutes || item.wait_minutes || 0),
      ticket_status: item.ticket_status || "なし",
      capacity_status: item.capacity_status || "通常",
      updated_at: item.updated_at || null,
    }))
    .sort((a, b) => a.current_wait_minutes - b.current_wait_minutes || a.exhibition_id - b.exhibition_id);
}

function updateCategories(items) {
  const selected = elements.category.value;
  const categories = Array.from(new Set(items.map((item) => item.category).filter(Boolean))).sort((a, b) =>
    a.localeCompare(b, "ja"),
  );
  elements.category.innerHTML = '<option value="">すべて</option>';
  for (const category of categories) {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    elements.category.append(option);
  }
  elements.category.value = categories.includes(selected) ? selected : "";
}

function filteredItems() {
  const query = elements.search.value.trim().toLowerCase();
  const category = elements.category.value;
  return allItems.filter((item) => {
    const matchesCategory = !category || item.category === category;
    const haystack = [item.exhibition_name, item.location_name, item.category].join(" ").toLowerCase();
    return matchesCategory && (!query || haystack.includes(query));
  });
}

function render() {
  const items = filteredItems();
  elements.list.innerHTML = items
    .map((item) => {
      const tone = waitTone(item.current_wait_minutes);
      return `
        <article class="wait-card tone-${tone}">
          <div>
            <h2>${escapeText(item.exhibition_name)}</h2>
            <p class="location">${escapeText(item.location_name)} / ${escapeText(item.category)}</p>
          </div>
          <div class="wait-value">
            <strong>${item.current_wait_minutes}<small>分</small></strong>
            <span>${waitLabel(item.current_wait_minutes)}</span>
          </div>
          <div class="wait-meta">
            <div><span>所要時間</span><strong>${item.duration_minutes || "--"}分</strong></div>
            <div><span>整理券</span><strong>${escapeText(item.ticket_status)}</strong></div>
            <div><span>定員</span><strong>${escapeText(item.capacity_status)}</strong></div>
            <div><span>企画ID</span><strong>${item.exhibition_id}</strong></div>
          </div>
        </article>
      `;
    })
    .join("");

  elements.empty.hidden = items.length > 0;
  elements.count.textContent = String(allItems.length);
  elements.quiet.textContent = String(allItems.filter((item) => item.current_wait_minutes <= 5).length);
  elements.max.textContent = `${Math.max(0, ...allItems.map((item) => item.current_wait_minutes))}分`;
}

async function refresh() {
  try {
    const data = await fetchWaitTimes();
    allItems = normalizeItems(data);
    updateCategories(allItems);
    render();
    elements.updated.textContent = new Date().toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    elements.connection.textContent = "接続確認中";
    if (!allItems.length) {
      allItems = normalizeItems(await loadJson("./wait_times.sample.json"));
      updateCategories(allItems);
      render();
    }
    console.warn(error);
  }
}

elements.search.addEventListener("input", render);
elements.category.addEventListener("change", render);

void refresh();
window.setInterval(refresh, REFRESH_MS);
