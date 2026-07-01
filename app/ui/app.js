const state = {
  results: [],
  source: "",
  total: 0,
  sortKey: "rank",
  sortDirection: "asc",
  query: "",
  risk: "all",
  displayLimit: 100,
  expanded: null,
};

const elements = {
  rows: document.querySelector("#candidateRows"),
  loading: document.querySelector("#loadingState"),
  empty: document.querySelector("#emptyState"),
  search: document.querySelector("#searchInput"),
  risk: document.querySelector("#riskFilter"),
  limit: document.querySelector("#displayLimit"),
  file: document.querySelector("#fileInput"),
  upload: document.querySelector("#uploadButton"),
  demo: document.querySelector("#demoButton"),
  export: document.querySelector("#exportButton"),
  count: document.querySelector("#resultsCount"),
  table: document.querySelector(".candidate-table"),
  drawer: document.querySelector("#methodDrawer"),
  backdrop: document.querySelector("#drawerBackdrop"),
  toast: document.querySelector("#toastRegion"),
};

const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, character => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
})[character]);

function initials(title) {
  const ignored = new Set(["senior", "lead", "principal", "founding", "ii", "staff"]);
  return title.split(/\s+/).filter(word => !ignored.has(word.toLowerCase())).slice(0, 2).map(word => word[0]).join("").toUpperCase() || "—";
}

function filteredResults() {
  const query = state.query.trim().toLowerCase();
  return state.results.filter(item => {
    const searchable = [item.candidate_id, item.current_title, item.current_company, item.location, ...(item.matched_skills || [])].join(" ").toLowerCase();
    const matchesSearch = !query || searchable.includes(query);
    const flagged = (item.disqualifier_flags || []).length + (item.honeypot_flags || []).length > 0;
    const matchesRisk = state.risk === "all"
      || (state.risk === "clean" && !flagged)
      || (state.risk === "flagged" && flagged)
      || (state.risk === "available" && item.availability_risk === "low");
    return matchesSearch && matchesRisk;
  }).sort((left, right) => {
    let a = left[state.sortKey];
    let b = right[state.sortKey];
    if (typeof a === "string") {
      a = a.toLowerCase();
      b = String(b).toLowerCase();
    }
    const order = a < b ? -1 : a > b ? 1 : String(left.candidate_id).localeCompare(String(right.candidate_id));
    return state.sortDirection === "asc" ? order : -order;
  });
}

function availabilityLabel(risk) {
  return risk === "low" ? "Reachable" : risk === "medium" ? "Review" : "At risk";
}

function rowTemplate(item) {
  const expanded = state.expanded === item.candidate_id;
  const flags = [...(item.disqualifier_flags || []), ...(item.honeypot_flags || [])];
  const breakdown = item.breakdown || {};
  const bars = [
    ["Retrieval relevance", breakdown.retrieval],
    ["Career skill evidence", breakdown.skills],
    ["Hidden-gem signal", breakdown.hidden_gem],
    ["Shipper signal", breakdown.shipper],
    ["Production depth", breakdown.production],
    ["Availability", breakdown.availability],
    ["Career quality", breakdown.career],
    ["Profile integrity", breakdown.integrity],
  ].map(([label, value]) => `
    <div class="bar-item">
      <div class="bar-label"><span>${escapeHtml(label)}</span><strong>${Number(value || 0).toFixed(0)}</strong></div>
      <div class="score-bar"><i style="--value:${Math.max(0, Math.min(100, Number(value || 0)))}%"></i></div>
    </div>`).join("");

  const tags = (item.matched_skills || []).map(skill => `<span class="tag">${escapeHtml(skill.replaceAll("_", " "))}</span>`).join("");
  const flagTags = flags.map(flag => `<span class="tag flag">${escapeHtml(flag.replaceAll("_", " "))}</span>`).join("");
  return `
    <tr class="candidate-row ${expanded ? "expanded" : ""}" data-candidate-id="${escapeHtml(item.candidate_id)}" tabindex="0" aria-expanded="${expanded}">
      <td><span class="rank-value ${item.rank <= 3 ? "top" : ""}">${String(item.rank).padStart(2, "0")}</span></td>
      <td>
        <div class="candidate-cell">
          <span class="candidate-avatar">${escapeHtml(initials(item.current_title))}</span>
          <span class="candidate-meta">
            <span class="candidate-title">${escapeHtml(item.current_title)}</span>
            <span class="candidate-subtitle">${escapeHtml(item.candidate_id)} · ${escapeHtml(item.current_company || "Company not specified")}</span>
          </span>
        </div>
      </td>
      <td class="numeric">${Number(item.years_of_experience).toFixed(1)} yrs<small>${escapeHtml(item.location || "Location n/a")}</small></td>
      <td><div class="score-wrap"><span class="score-value">${Number(item.score).toFixed(1)}</span><span class="mini-meter"><i style="--score:${Math.min(100, Number(item.score))}%"></i></span></div></td>
      <td><span class="badge ${escapeHtml(item.availability_risk)}">${availabilityLabel(item.availability_risk)}</span></td>
      <td><div class="reasoning">${escapeHtml(item.reasoning)}</div></td>
      <td><button class="expand-button" aria-label="${expanded ? "Collapse" : "Expand"} ${escapeHtml(item.candidate_id)} details"><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="m3.5 5 3.5 3.5L10.5 5" fill="none" stroke="currentColor" stroke-width="1.3"/></svg></button></td>
    </tr>
    ${expanded ? `<tr class="detail-row"><td colspan="7"><div class="detail-panel">
      <div>
        <div class="detail-heading"><h3>Score anatomy</h3><span>WEIGHTED / GATED / NORMALIZED</span></div>
        <div class="breakdown-grid">${bars}</div>
      </div>
      <div class="evidence-box">
        <div class="detail-heading"><h3>Decision note</h3><span>${escapeHtml(item.candidate_id)}</span></div>
        <p>${escapeHtml(item.reasoning)}</p>
        <div class="tag-list">${tags || '<span class="tag">No direct skill match</span>'}${flagTags}</div>
      </div>
    </div></td></tr>` : ""}`;
}

function render() {
  const matchingResults = filteredResults();
  const results = matchingResults.slice(0, state.displayLimit);
  elements.rows.innerHTML = results.map(rowTemplate).join("");
  elements.empty.hidden = results.length > 0;
  elements.count.textContent = `${results.length} shown · ${matchingResults.length} match filters · ${state.results.length} ranked`;
  elements.rows.querySelectorAll(".candidate-row").forEach(row => {
    const toggle = () => {
      state.expanded = state.expanded === row.dataset.candidateId ? null : row.dataset.candidateId;
      render();
    };
    row.addEventListener("click", toggle);
    row.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    });
  });
}

function renderMetrics() {
  const results = state.results;
  const hiddenGems = results.filter(item => (item.breakdown?.hidden_gem || 0) >= 55 && !/(ml|ai|data scientist|applied scientist)/i.test(item.current_title)).length;
  const flagged = results.filter(item => (item.disqualifier_flags || []).length + (item.honeypot_flags || []).length).length;
  document.querySelector("#metricTotal").textContent = state.total || results.length;
  document.querySelector("#metricSource").textContent = state.source.includes("demo") ? "DEMO SET" : "UPLOADED";
  document.querySelector("#metricTop").textContent = results.length ? Number(results[0].score).toFixed(1) : "—";
  document.querySelector("#metricTopId").textContent = results.length ? `${results[0].candidate_id} · ${results[0].current_title}` : "Awaiting ranking";
  document.querySelector("#metricGems").textContent = hiddenGems;
  document.querySelector("#metricFlags").textContent = flagged;
}

async function loadDemo() {
  setLoading(true);
  try {
    const response = await fetch("/api/demo");
    if (!response.ok) throw new Error(`Demo request failed (${response.status})`);
    acceptPayload(await response.json());
    showToast("Curated ranking loaded. Open any row to audit its score.");
  } catch (error) {
    showError(error.message || "Could not load demo data");
  } finally {
    setLoading(false);
  }
}

async function uploadCandidates(file) {
  if (!file) return;
  setLoading(true);
  const form = new FormData();
  form.append("file", file);
  try {
    const response = await fetch("/api/rank", { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Ranking failed");
    acceptPayload(payload);
    showToast(`${payload.total} profiles ranked from ${file.name}.`);
  } catch (error) {
    showError(error.message || "Could not rank this file");
  } finally {
    elements.file.value = "";
    setLoading(false);
  }
}

function acceptPayload(payload) {
  state.results = payload.results || [];
  state.source = payload.source || "ranking";
  state.total = payload.total || state.results.length;
  state.expanded = null;
  elements.limit.max = Math.max(1, state.results.length);
  state.displayLimit = Math.min(Math.max(1, Number(elements.limit.value) || 100), Math.max(1, state.results.length));
  elements.limit.value = state.displayLimit;
  renderMetrics();
  render();
}

function setLoading(isLoading) {
  elements.loading.hidden = !isLoading;
  elements.rows.hidden = isLoading;
  elements.upload.disabled = isLoading;
  elements.demo.disabled = isLoading;
  if (isLoading) elements.empty.hidden = true;
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  elements.toast.appendChild(toast);
  window.setTimeout(() => toast.remove(), 4200);
}
const showError = message => showToast(message, "error");

function exportCsv() {
  if (!state.results.length) return showError("There is no ranking to export yet.");
  const quote = value => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const rows = ["candidate_id,rank,score,reasoning", ...state.results.map(item => [item.candidate_id, item.rank, item.score.toFixed(6), item.reasoning].map(quote).join(","))];
  const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "submission-preview.csv";
  link.click();
  URL.revokeObjectURL(link.href);
  showToast("CSV preview exported.");
}

function openDrawer() {
  elements.backdrop.hidden = false;
  requestAnimationFrame(() => {
    elements.backdrop.classList.add("visible");
    elements.drawer.classList.add("open");
    elements.drawer.setAttribute("aria-hidden", "false");
    document.querySelector("#closeDrawer").focus();
  });
}
function closeDrawer() {
  elements.backdrop.classList.remove("visible");
  elements.drawer.classList.remove("open");
  elements.drawer.setAttribute("aria-hidden", "true");
  window.setTimeout(() => { elements.backdrop.hidden = true; }, 220);
}

elements.search.addEventListener("input", event => { state.query = event.target.value; state.expanded = null; render(); });
elements.risk.addEventListener("change", event => { state.risk = event.target.value; state.expanded = null; render(); });
function updateDisplayLimit(event) {
  if (event.target.value === "") return;
  const available = Math.max(1, state.results.length);
  state.displayLimit = Math.min(available, Math.max(1, Math.floor(Number(event.target.value) || 100)));
  event.target.value = state.displayLimit;
  state.expanded = null;
  render();
}
elements.limit.addEventListener("input", updateDisplayLimit);
elements.limit.addEventListener("change", updateDisplayLimit);
elements.upload.addEventListener("click", () => elements.file.click());
elements.file.addEventListener("change", event => uploadCandidates(event.target.files[0]));
elements.demo.addEventListener("click", loadDemo);
elements.export.addEventListener("click", exportCsv);
document.querySelector("#clearFilters").addEventListener("click", () => { state.query = ""; state.risk = "all"; elements.search.value = ""; elements.risk.value = "all"; render(); });
document.querySelectorAll("[data-sort]").forEach(button => button.addEventListener("click", () => {
  const key = button.dataset.sort;
  state.sortDirection = state.sortKey === key && state.sortDirection === "asc" ? "desc" : "asc";
  state.sortKey = key;
  render();
}));
document.querySelectorAll("[data-density]").forEach(button => button.addEventListener("click", () => {
  document.querySelectorAll("[data-density]").forEach(item => item.classList.toggle("active", item === button));
  elements.table.classList.toggle("compact", button.dataset.density === "compact");
}));
document.querySelectorAll("[data-open-method], [data-open-validation]").forEach(button => button.addEventListener("click", openDrawer));
document.querySelector("#closeDrawer").addEventListener("click", closeDrawer);
elements.backdrop.addEventListener("click", closeDrawer);
document.addEventListener("keydown", event => {
  if (event.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) {
    event.preventDefault();
    elements.search.focus();
  }
  if (event.key === "Escape") closeDrawer();
});
document.querySelector("[data-scroll]").addEventListener("click", () => document.querySelector("#rankings").scrollIntoView({ behavior: "smooth" }));

elements.table.classList.add("compact");
loadDemo();

// Theme Toggle
const themeToggleBtn = document.querySelector("#themeToggle");
const iconSun = themeToggleBtn.querySelector(".icon-sun");
const iconMoon = themeToggleBtn.querySelector(".icon-moon");

function setTheme(isDark) {
  if (isDark) {
    document.body.classList.add("dark-theme");
    iconMoon.style.display = "none";
    iconSun.style.display = "block";
  } else {
    document.body.classList.remove("dark-theme");
    iconMoon.style.display = "block";
    iconSun.style.display = "none";
  }
  localStorage.setItem("theme", isDark ? "dark" : "light");
}

const storedTheme = localStorage.getItem("theme");
setTheme(storedTheme === "dark");

themeToggleBtn.addEventListener("click", () => {
  const isDark = document.body.classList.contains("dark-theme");
  setTheme(!isDark);
});
