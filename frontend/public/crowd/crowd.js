import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
import {
  getDatabase,
  push,
  ref,
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-database.js";

const STATUS_LABELS = {
  empty: "すぐ入れそう",
  short: "少し待つ",
  busy: "かなり混んでいる",
  closed: "受付停止・満員っぽい",
};

const state = {
  exhibitions: [],
  filtered: [],
  selectedId: "",
  selectedStatus: "",
  database: null,
  configReady: false,
  sending: false,
};

const elements = {
  configNotice: document.querySelector("#configNotice"),
  exhibitionSelect: document.querySelector("#exhibitionSelect"),
  searchInput: document.querySelector("#searchInput"),
  selectedCard: document.querySelector("#selectedCard"),
  selectedCategory: document.querySelector("#selectedCategory"),
  selectedName: document.querySelector("#selectedName"),
  selectedLocation: document.querySelector("#selectedLocation"),
  statusButtons: document.querySelector("#statusButtons"),
  submitButton: document.querySelector("#submitButton"),
  messageBox: document.querySelector("#messageBox"),
};

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} could not be loaded`);
  }
  return response.json();
}

async function loadConfig() {
  try {
    const config = await fetchJson("./firebase_config.json");
    state.database = getDatabase(initializeApp(config));
    state.configReady = true;
    updateSubmitState();
  } catch (error) {
    elements.configNotice.hidden = false;
    elements.submitButton.disabled = true;
    state.configReady = false;
    updateSubmitState();
  }
}

async function loadExhibitions() {
  state.exhibitions = await fetchJson("./exhibitions.json");
  state.filtered = [...state.exhibitions];

  const requestedId = new URLSearchParams(location.search).get("id");
  if (requestedId && state.exhibitions.some((item) => String(item.id) === requestedId)) {
    state.selectedId = requestedId;
  }

  renderExhibitionOptions();
  renderSelectedExhibition();
}

function renderExhibitionOptions() {
  const selectedStillVisible = state.filtered.some(
    (item) => String(item.id) === state.selectedId,
  );

  elements.exhibitionSelect.innerHTML = "";
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "企画を選択してください";
  elements.exhibitionSelect.append(placeholder);

  for (const exhibition of state.filtered) {
    const option = document.createElement("option");
    option.value = String(exhibition.id);
    option.textContent = `${exhibition.name} / ${exhibition.location_name}`;
    elements.exhibitionSelect.append(option);
  }

  elements.exhibitionSelect.value = selectedStillVisible ? state.selectedId : "";
}

function renderSelectedExhibition() {
  const exhibition = getSelectedExhibition();
  elements.selectedCard.hidden = !exhibition;

  if (exhibition) {
    elements.selectedCategory.textContent = exhibition.category;
    elements.selectedName.textContent = exhibition.name;
    elements.selectedLocation.textContent = exhibition.location_name;
  }

  updateSubmitState();
}

function getSelectedExhibition() {
  return state.exhibitions.find((item) => String(item.id) === state.selectedId);
}

function updateSubmitState() {
  elements.submitButton.disabled =
    !state.configReady ||
    state.sending ||
    !state.selectedId ||
    !state.selectedStatus;
}

function setMessage(text, isError = false) {
  elements.messageBox.hidden = false;
  elements.messageBox.textContent = text;
  elements.messageBox.classList.toggle("error", isError);
}

function filterExhibitions() {
  const query = elements.searchInput.value.trim().toLowerCase();
  state.filtered = state.exhibitions.filter((item) => {
    const haystack = `${item.name} ${item.category} ${item.location_name}`.toLowerCase();
    return haystack.includes(query);
  });
  renderExhibitionOptions();
}

function selectStatus(status) {
  state.selectedStatus = status;
  for (const button of elements.statusButtons.querySelectorAll("button")) {
    button.setAttribute("aria-pressed", String(button.dataset.status === status));
  }
  updateSubmitState();
}

async function submitReport() {
  const exhibition = getSelectedExhibition();
  if (!exhibition || !state.selectedStatus || !state.database) {
    updateSubmitState();
    return;
  }

  state.sending = true;
  updateSubmitState();
  setMessage("送信しています...");

  const report = {
    exhibitionId: exhibition.id,
    status: state.selectedStatus,
    createdAt: Date.now(),
  };

  try {
    await push(ref(state.database, `crowdReports/${exhibition.id}`), report);
    setMessage(
      `ありがとうございます。「${exhibition.name}」を「${STATUS_LABELS[state.selectedStatus]}」として受け付けました。`,
    );
    state.selectedStatus = "";
    selectStatus("");
  } catch (error) {
    setMessage("送信できませんでした。通信状況を確認して、もう一度お試しください。", true);
  } finally {
    state.sending = false;
    updateSubmitState();
  }
}

elements.exhibitionSelect.addEventListener("change", (event) => {
  state.selectedId = event.target.value;
  renderSelectedExhibition();
});

elements.searchInput.addEventListener("input", filterExhibitions);

elements.statusButtons.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-status]");
  if (!button) {
    return;
  }
  selectStatus(button.dataset.status);
});

elements.submitButton.addEventListener("click", submitReport);

Promise.all([loadConfig(), loadExhibitions()]).catch(() => {
  elements.exhibitionSelect.innerHTML = '<option value="">企画一覧を読み込めませんでした</option>';
  setMessage("企画一覧を読み込めませんでした。時間をおいて再読み込みしてください。", true);
});
