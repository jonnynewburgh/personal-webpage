'use strict';

// ── State ─────────────────────────────────────────────────────────
const state = {
  tab: 'search',
  results: [],
  activeJobs: {},   // job_id → { es, card }
  pendingImport: null,   // { dataset, tableCandidate }
};

// ── DOM helpers ───────────────────────────────────────────────────
const $  = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const el = (tag, cls = '', html = '') => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  return e;
};

// ── API ───────────────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  const r = await fetch(path, opts);
  if (!r.ok) {
    let msg = r.statusText;
    try { const d = await r.json(); msg = d.detail?.message || d.detail || msg; } catch {}
    throw new Error(msg);
  }
  return r.json();
}

// ── Tab navigation ────────────────────────────────────────────────
function switchTab(tab) {
  state.tab = tab;
  $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.tab === tab));
  $$('.panel').forEach(p => p.classList.toggle('active', p.id === `panel-${tab}`));
  if (tab === 'tables') loadTables();
}

// ── Search tab ────────────────────────────────────────────────────
async function doSearch() {
  const source  = $('#source-select').value;
  const query   = $('#search-input').value.trim();
  if (!query) return;

  const btn = $('#search-btn');
  btn.disabled = true;
  btn.textContent = 'Searching…';
  clearError('search');
  renderResults([]);

  try {
    const results = await api('GET', `/api/search/${source}?q=${encodeURIComponent(query)}&limit=25`);
    state.results = results;
    renderResults(results);
  } catch (e) {
    showError('search', e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Search';
  }
}

async function probeUrl() {
  const url = $('#url-input').value.trim();
  if (!url) return;

  const btn = $('#probe-btn');
  btn.disabled = true;
  btn.textContent = 'Probing…';
  clearError('search');
  $('#table-chooser').innerHTML = '';

  try {
    const info = await api('POST', '/api/search/url', { url });

    if (info.detected_type === 'html' && info.html_tables?.length) {
      renderTableChooser(url, info.html_tables);
    } else {
      // Treat as direct download
      const pseudo = {
        id: url,
        title: url.split('/').pop() || url,
        description: `Direct ${info.detected_type.toUpperCase()} download`,
        source_type: 'url',
        download_url: url,
        file_format: info.detected_type,
      };
      state.results = [pseudo];
      renderResults([pseudo]);
    }
  } catch (e) {
    showError('search', e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Probe';
  }
}

function renderResults(results) {
  const list = $('#results-list');
  list.innerHTML = '';

  if (!results.length) {
    list.innerHTML = '<div class="empty">No results yet. Try a search above.</div>';
    return;
  }

  results.forEach(ds => {
    const card = el('div', 'result-card');
    const fmt = ds.file_format ? `<span class="badge">${ds.file_format}</span>` : '';
    card.innerHTML = `
      <div class="result-meta">
        <div class="result-title" title="${esc(ds.title)}">${esc(ds.title)}</div>
        <div class="result-desc">${esc(ds.description || '')}</div>
      </div>
      <div class="result-actions">
        ${fmt}
        <button class="btn-primary btn-sm import-btn">Import</button>
      </div>`;
    $('.import-btn', card).addEventListener('click', () => openImportDialog(ds));
    list.appendChild(card);
  });
}

function renderTableChooser(url, tables) {
  const wrap = $('#table-chooser');
  wrap.innerHTML = '';
  const box = el('div', 'table-chooser');
  box.innerHTML = `<h3>Found ${tables.length} table(s) on this page — choose one to import:</h3>`;

  tables.forEach(t => {
    const row = el('div', 'table-candidate');
    row.innerHTML = `
      <div>
        <div>Table #${t.index}</div>
        <div class="tc-info">${t.rows} rows × ${t.cols} cols</div>
        <div class="tc-headers">${esc(t.headers.slice(0, 6).join(', '))}${t.headers.length > 6 ? '…' : ''}</div>
      </div>`;
    const btn = el('button', 'btn-primary btn-sm');
    btn.textContent = 'Import this';
    btn.addEventListener('click', () => {
      const ds = {
        id: url,
        title: `Table ${t.index} from ${url.split('/').pop() || url}`,
        description: `HTML table ${t.index}: ${t.rows} rows`,
        source_type: 'html_table',
        download_url: url,
        file_format: 'html',
        table_index: t.index,
      };
      openImportDialog(ds, t.index);
    });
    row.appendChild(btn);
    box.appendChild(row);
  });
  wrap.appendChild(box);
}

// ── Import dialog ─────────────────────────────────────────────────
function openImportDialog(ds, tableIndex = null) {
  closeImportDialog();
  const suggestedName = slugify(ds.title);
  const dialog = el('div', 'import-dialog');
  dialog.id = 'import-dialog';
  dialog.innerHTML = `
    <div><strong>Import: </strong>${esc(ds.title)}</div>
    <label>Table name in SQLite:</label>
    <input type="text" id="import-name" value="${esc(suggestedName)}" maxlength="64" />
    <div style="display:flex;gap:8px">
      <button class="btn-primary" id="confirm-import-btn">Start Import</button>
      <button class="btn-ghost" id="cancel-import-btn">Cancel</button>
    </div>`;

  $('#results-list').before(dialog);

  $('#confirm-import-btn').addEventListener('click', () => {
    const tableName = $('#import-name').value.trim();
    if (!tableName) return;
    closeImportDialog();
    startImport({ ...ds, table_index: tableIndex }, tableName);
  });
  $('#cancel-import-btn').addEventListener('click', closeImportDialog);
}

function closeImportDialog() {
  const d = $('#import-dialog');
  if (d) d.remove();
}

// ── Download / SSE progress ───────────────────────────────────────
async function startImport(ds, tableName) {
  const req = {
    source_type: ds.source_type,
    download_url: ds.download_url,
    table_name: tableName,
    dataset_id: ds.source_type === 'kaggle' ? ds.id : null,
    table_index: ds.table_index ?? null,
    file_format: ds.file_format || null,
  };

  let jobId;
  try {
    const resp = await api('POST', '/api/download', req);
    jobId = resp.job_id;
  } catch (e) {
    showError('search', `Failed to start import: ${e.message}`);
    return;
  }

  const progressArea = $('#progress-area');
  const progressId = `job-${jobId}`;
  const card = el('div', 'progress-area');
  card.id = progressId;
  card.innerHTML = `
    <div class="progress-header">
      <span>${esc(tableName)}</span><span class="pct-label">0%</span>
    </div>
    <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:0%"></div></div>
    <div class="progress-msg">Starting…</div>`;
  progressArea.appendChild(card);

  const es = new EventSource(`/api/download/progress/${jobId}`);
  state.activeJobs[jobId] = es;

  es.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    const fill = $('.progress-bar-fill', card);
    const pct  = $('.pct-label', card);
    const msg  = $('.progress-msg', card);

    fill.style.width = `${ev.percent}%`;
    pct.textContent  = `${ev.percent}%`;
    msg.textContent  = ev.message;

    card.classList.remove('progress-done', 'progress-error');
    if (ev.phase === 'done') {
      card.classList.add('progress-done');
      es.close();
      delete state.activeJobs[jobId];
      // Auto-switch to tables after 2s
      setTimeout(() => { switchTab('tables'); card.remove(); }, 2000);
    } else if (ev.phase === 'error') {
      card.classList.add('progress-error');
      es.close();
      delete state.activeJobs[jobId];
    }
  };

  es.onerror = () => {
    $('.progress-msg', card).textContent = 'Connection lost.';
    card.classList.add('progress-error');
    es.close();
    delete state.activeJobs[jobId];
  };
}

// ── Tables tab ────────────────────────────────────────────────────
async function loadTables() {
  const list = $('#tables-list');
  list.innerHTML = '<div class="empty">Loading…</div>';
  try {
    const tables = await api('GET', '/api/tables');
    renderTables(tables);
  } catch (e) {
    list.innerHTML = `<div class="error-msg">${esc(e.message)}</div>`;
  }
}

function renderTables(tables) {
  const list = $('#tables-list');
  list.innerHTML = '';
  if (!tables.length) {
    list.innerHTML = '<div class="empty">No tables yet. Import some data first.</div>';
    return;
  }

  tables.forEach(t => {
    const row = el('div', 'table-row');
    row.innerHTML = `
      <div class="table-row-meta">
        <div class="table-row-name">${esc(t.name)}</div>
        <div class="table-row-stats">${t.row_count.toLocaleString()} rows · ${t.columns.length} columns</div>
      </div>
      <div class="table-row-actions">
        <button class="btn-ghost btn-sm preview-btn">Preview</button>
        <button class="btn-danger btn-sm delete-btn">Delete</button>
      </div>`;

    $('.preview-btn', row).addEventListener('click', () => previewTable(t.name));
    $('.delete-btn', row).addEventListener('click', async () => {
      if (!confirm(`Delete table "${t.name}"? This cannot be undone.`)) return;
      await api('DELETE', `/api/tables/${encodeURIComponent(t.name)}`);
      closePreview();
      loadTables();
    });
    list.appendChild(row);
  });
}

async function previewTable(name) {
  closePreview();
  const wrap = el('div', 'preview-wrap');
  wrap.id = 'preview-wrap';
  wrap.innerHTML = `<h3>Preview: ${esc(name)} <span style="float:right;cursor:pointer" onclick="closePreview()">✕</span></h3>
    <div style="padding:16px;color:var(--muted)">Loading…</div>`;
  $('#tables-list').after(wrap);

  try {
    const data = await api('GET', `/api/tables/${encodeURIComponent(name)}/preview?rows=50`);
    const tbl = el('table', 'data-table');
    tbl.innerHTML = `<thead><tr>${data.columns.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
      <tbody>${data.rows.map(r => `<tr>${r.map(v => `<td title="${esc(String(v ?? ''))}">${esc(String(v ?? ''))}</td>`).join('')}</tr>`).join('')}</tbody>`;
    wrap.querySelector('div').replaceWith(tbl);
  } catch (e) {
    wrap.querySelector('div').innerHTML = `<span style="color:var(--danger)">${esc(e.message)}</span>`;
  }
}

function closePreview() {
  const w = $('#preview-wrap');
  if (w) w.remove();
}

// ── Utilities ─────────────────────────────────────────────────────
function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 64) || 'dataset';
}

function showError(scope, msg) {
  const el2 = $(`#${scope}-error`);
  if (!el2) return;
  el2.textContent = msg;
  el2.style.display = 'block';
}

function clearError(scope) {
  const el2 = $(`#${scope}-error`);
  if (!el2) return;
  el2.textContent = '';
  el2.style.display = 'none';
}

// ── Bootstrap ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Tab switching
  $$('.nav-item').forEach(n => {
    n.addEventListener('click', () => switchTab(n.dataset.tab));
  });

  // Search
  $('#search-btn').addEventListener('click', doSearch);
  $('#search-input').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

  // URL probe
  $('#probe-btn').addEventListener('click', probeUrl);
  $('#url-input').addEventListener('keydown', e => { if (e.key === 'Enter') probeUrl(); });

  switchTab('search');
});
