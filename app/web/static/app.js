"use strict";

const $ = (sel) => document.querySelector(sel);
const PROFILE_KEY = "tt_profiles";

const state = {
  file: null,
  presets: {},
  editable: [],
  catalog: [],
  report: null,
  view: "changed",
};

// ---------- init ----------
async function init() {
  const cfg = await (await fetch("/api/config")).json();
  state.presets = cfg.presets;
  state.editable = cfg.editable_rules;
  state.catalog = cfg.catalog;

  const sel = $("#preset");
  Object.keys(cfg.presets).forEach((name) => {
    const o = document.createElement("option");
    o.value = name;
    o.textContent = name[0].toUpperCase() + name.slice(1);
    sel.appendChild(o);
  });
  sel.value = state.presets.balanced ? "balanced" : Object.keys(state.presets)[0];
  sel.addEventListener("change", () => { syncRulesToPreset(); describePreset(); });

  buildRuleToggles();
  syncRulesToPreset();
  describePreset();
  wireUpload();
  wireProfiles();
  $("#run").addEventListener("click", runTransform);
  $("#report-btn").addEventListener("click", downloadReport);
  $("#reset-btn").addEventListener("click", resetAll);
  $("#viewtoggle").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => setView(b.dataset.view)));
}

const PRESET_NOTES = {
  conservative: "Only the safest, highest-confidence edits.",
  balanced: "Safe cleanups, transitions, and concision. Recommended.",
  strong: "More stylistic latitude, still meaning-preserving.",
  academic: "Concision and structure; scaffolds left intact.",
};
function describePreset() {
  $("#preset-hint").textContent = PRESET_NOTES[$("#preset").value] || "";
}

function buildRuleToggles() {
  const wrap = $("#rules");
  wrap.innerHTML = "";
  const byId = Object.fromEntries(state.catalog.map((r) => [r.id, r]));
  state.editable.forEach((id) => {
    const meta = byId[id] || { id, name: id, confidence: "high" };
    const row = document.createElement("label");
    row.className = "rule";
    row.innerHTML = `
      <input type="checkbox" data-rule="${id}" />
      <span class="r-name">${escapeHtml(meta.name)}</span>
      <span class="r-conf ${meta.confidence}">${meta.confidence}</span>`;
    wrap.appendChild(row);
  });
}

function syncRulesToPreset() {
  const preset = state.presets[$("#preset").value] || {};
  document.querySelectorAll("#rules input[data-rule]").forEach((cb) => {
    cb.checked = !!preset[cb.dataset.rule];
  });
}

function applyOverrides(overrides) {
  document.querySelectorAll("#rules input[data-rule]").forEach((cb) => {
    if (cb.dataset.rule in overrides) cb.checked = !!overrides[cb.dataset.rule];
  });
}

function currentOverrides() {
  const map = {};
  document.querySelectorAll("#rules input[data-rule]").forEach((cb) => {
    map[cb.dataset.rule] = cb.checked;
  });
  return map;
}

// ---------- upload ----------
function wireUpload() {
  const drop = $("#drop");
  const input = $("#file");
  input.addEventListener("change", () => setFile(input.files[0]));
  ["dragenter", "dragover"].forEach((e) =>
    drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add("hover"); }));
  ["dragleave", "drop"].forEach((e) =>
    drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.remove("hover"); }));
  drop.addEventListener("drop", (ev) => setFile(ev.dataTransfer.files[0]));
}

function setFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".docx")) {
    setStatus("Please choose a .docx file.", true);
    return;
  }
  state.file = file;
  $("#filename").textContent = file.name;
  $("#run").disabled = false;
  setStatus("");
}

// ---------- profiles (localStorage) ----------
function loadProfiles() {
  try { return JSON.parse(localStorage.getItem(PROFILE_KEY)) || {}; }
  catch { return {}; }
}
function saveProfiles(p) { localStorage.setItem(PROFILE_KEY, JSON.stringify(p)); }

function refreshProfileList() {
  const sel = $("#profiles");
  const names = Object.keys(loadProfiles()).sort();
  sel.innerHTML = `<option value="">Saved profiles…</option>` +
    names.map((n) => `<option value="${escapeHtml(n)}">${escapeHtml(n)}</option>`).join("");
}

function wireProfiles() {
  refreshProfileList();
  $("#saveprof").addEventListener("click", () => {
    const name = $("#profname").value.trim();
    if (!name) { setStatus("Name the profile first.", true); return; }
    const all = loadProfiles();
    all[name] = { preset: $("#preset").value, overrides: currentOverrides() };
    saveProfiles(all);
    $("#profname").value = "";
    refreshProfileList();
    $("#profiles").value = name;
    setStatus(`Saved profile “${name}”.`);
  });
  $("#loadprof").addEventListener("click", () => {
    const name = $("#profiles").value;
    if (!name) return;
    const prof = loadProfiles()[name];
    if (!prof) return;
    if (prof.preset && state.presets[prof.preset]) {
      $("#preset").value = prof.preset;
      describePreset();
    }
    applyOverrides(prof.overrides || {});
    setStatus(`Loaded profile “${name}”.`);
  });
  $("#delprof").addEventListener("click", () => {
    const name = $("#profiles").value;
    if (!name) return;
    const all = loadProfiles();
    delete all[name];
    saveProfiles(all);
    refreshProfileList();
    setStatus(`Deleted profile “${name}”.`);
  });
}

// ---------- run ----------
async function runTransform() {
  if (!state.file) return;
  setStatus("Transforming…");
  $("#run").disabled = true;

  const fd = new FormData();
  fd.append("file", state.file);
  fd.append("preset", $("#preset").value);
  fd.append("overrides", JSON.stringify(currentOverrides()));

  try {
    const res = await fetch("/api/transform", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Transform failed.");
    state.report = data;
    render(data);
    setStatus(`Done — ${data.summary.edits_applied} edit(s) applied.`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    $("#run").disabled = false;
  }
}

function downloadReport() {
  if (!state.report) return;
  const blob = new Blob([JSON.stringify(state.report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = (state.report.download_name || "report").replace(/\.docx$/, "") + ".report.json";
  a.click();
  URL.revokeObjectURL(url);
}

function resetAll() {
  state.file = null;
  state.report = null;
  $("#file").value = "";
  $("#filename").textContent = "";
  $("#run").disabled = true;
  $("#export-wrap").hidden = true;
  $("#viewtoggle").hidden = true;
  $("#diff").innerHTML = `<div class="empty">Upload a document and press <em>Transform</em> to see changes.</div>`;
  $("#stats").innerHTML = `<div class="empty">No document yet.</div>`;
  $("#changes").innerHTML = `<div class="empty">—</div>`;
  $("#flags").innerHTML = `<div class="empty">—</div>`;
  $("#warnings").innerHTML = "";
  $("#warn-head").hidden = true;
  setStatus("");
}

// ---------- render ----------
function render(r) {
  renderStats(r);
  renderDiff(r);
  renderChanges(r);
  renderFlags(r);
  renderWarnings(r);

  const dl = $("#download");
  dl.href = `/api/download/${r.token}`;
  dl.setAttribute("download", r.download_name);
  $("#export-wrap").hidden = false;
  $("#viewtoggle").hidden = false;
}

function renderStats(r) {
  const s = r.stats;
  const cells = [
    ["Edits", r.summary.edits_applied],
    ["Suggestions", r.summary.flags],
    ["Words", s.words],
    ["Avg sentence", s.avg_sentence_len],
  ];
  let html = cells.map(([k, v]) =>
    `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
  html += `<div class="chips">
      <span class="chip">Type: ${escapeHtml(r.doc_type)}</span>
      <span class="chip">Tone: ${escapeHtml(r.tone)}</span>
      <span class="chip">${s.paragraphs} paras</span>
      <span class="chip">${s.citations} citation(s)</span>
    </div>`;
  $("#stats").innerHTML = html;
}

function renderDiff(r) {
  const host = $("#diff");
  const paras = r.paragraphs.filter((p) =>
    state.view === "all" ? true : p.changed);
  if (!paras.length) {
    host.innerHTML = `<div class="empty">No changes to show in this view.</div>`;
    return;
  }
  host.innerHTML = paras.map((p) => {
    const isHeading = ["heading", "title", "caption"].includes(p.block_type);
    const cls = p.changed ? "pair" : "pair unchanged";
    let [before, after] = wordDiff(p.original, p.transformed);
    before = highlightLocks(before, p.protected);
    after = highlightLocks(after, p.protected);
    const hcls = isHeading ? "heading" : "";
    return `<div class="${cls}">
      <div class="cell before ${hcls}"><span class="cap">before · para ${p.index}</span><span class="body">${before}</span></div>
      <div class="cell after ${hcls}"><span class="cap">after</span><span class="body">${after}</span></div>
    </div>`;
  }).join("");
}

function renderChanges(r) {
  const host = $("#changes");
  if (!r.changes.length) { host.innerHTML = `<div class="empty">No edits applied.</div>`; return; }
  host.innerHTML = r.changes.map((c) => `
    <div class="entry">
      <div class="e-top"><span class="e-rule">${escapeHtml(c.rule_name)}</span>
        <span class="e-loc">para ${c.paragraph_index} · ${c.confidence}</span></div>
      <div><code>${escapeHtml(c.before)}</code></div>
      <div>→ <code>${escapeHtml(c.after)}</code></div>
      <div class="e-reason">${escapeHtml(c.reason)}</div>
    </div>`).join("");
}

function renderFlags(r) {
  const host = $("#flags");
  if (!r.flags.length) { host.innerHTML = `<div class="empty">None.</div>`; return; }
  host.innerHTML = r.flags.map((f) => `
    <div class="entry flag">
      <div class="e-top"><span class="e-rule">${escapeHtml(f.message)}</span>
        <span class="e-loc">para ${f.paragraph_index}</span></div>
      ${f.excerpt ? `<div class="e-reason">…${escapeHtml(f.excerpt)}…</div>` : ""}
    </div>`).join("");
}

function renderWarnings(r) {
  const all = [...r.issues, ...r.rejected];
  const host = $("#warnings");
  $("#warn-head").hidden = all.length === 0;
  host.innerHTML = all.map((i) => `
    <div class="entry warn">
      <div class="e-top"><span class="e-rule">${escapeHtml(i.level.toUpperCase())}</span>
        <span class="e-loc">${i.paragraph_index < 0 ? "document" : "para " + i.paragraph_index}</span></div>
      <div class="e-reason">${escapeHtml(i.message)}</div>
    </div>`).join("");
}

function setView(v) {
  state.view = v;
  $("#viewtoggle").querySelectorAll("button").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === v));
  if (state.report) renderDiff(state.report);
}

// ---------- word-level diff ----------
function wordDiff(a, b) {
  const at = a.match(/\S+|\s+/g) || [];
  const bt = b.match(/\S+|\s+/g) || [];
  const n = at.length, m = bt.length;
  const dp = Array.from({ length: n + 1 }, () => new Int32Array(m + 1));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      dp[i][j] = at[i] === bt[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  let i = 0, j = 0, before = "", after = "";
  while (i < n && j < m) {
    if (at[i] === bt[j]) { before += escapeHtml(at[i]); after += escapeHtml(bt[j]); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { before += `<del>${escapeHtml(at[i])}</del>`; i++; }
    else { after += `<ins>${escapeHtml(bt[j])}</ins>`; j++; }
  }
  while (i < n) { before += `<del>${escapeHtml(at[i++])}</del>`; }
  while (j < m) { after += `<ins>${escapeHtml(bt[j++])}</ins>`; }
  return [before || "<span class='cap'>(empty)</span>", after || "<span class='cap'>(empty)</span>"];
}

// Wrap protected substrings (sorted longest-first) in the diff HTML. Protected
// content is verbatim and sits in the common (untagged) runs, so an escaped
// substring replace lands cleanly. Each match becomes a private-use sentinel
// first, then expands to markup, so a shorter lock can't re-wrap inside a
// longer one already handled.
const _S0 = String.fromCharCode(0xE000);
const _S1 = String.fromCharCode(0xE001);
const _SENTINEL = new RegExp(_S0 + "(\\d+)" + _S1, "g");
function highlightLocks(html, locks) {
  if (!locks || !locks.length) return html;
  const marks = [];
  for (const lock of locks) {
    const esc = escapeHtml(lock);
    if (!esc) continue;
    const idx = marks.length;
    const next = html.split(esc).join(_S0 + idx + _S1);
    if (next !== html) { marks.push(esc); html = next; }
  }
  return html.replace(_SENTINEL,
    (_, i) => `<span class="lock">${marks[Number(i)]}</span>`);
}

// ---------- utils ----------
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function setStatus(msg, isErr) {
  const el = $("#status");
  el.textContent = msg;
  el.classList.toggle("err", !!isErr);
}

init();
