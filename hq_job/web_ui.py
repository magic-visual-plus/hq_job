
# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HQ Job Manager</title>
<style>
  :root {
    --bg: #f5f7fa; --card: #fff; --border: #e2e8f0; --primary: #3b82f6;
    --primary-hover: #2563eb; --danger: #ef4444; --danger-hover: #dc2626;
    --success: #22c55e; --warning: #f59e0b; --gray: #6b7280;
    --text: #1e293b; --text-light: #64748b; --radius: 8px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.5; }

  /* Header */
  .header { background: var(--card); border-bottom: 1px solid var(--border);
            padding: 12px 24px; display: flex; align-items: center; gap: 16px;
            position: sticky; top: 0; z-index: 10; }
  .header h1 { font-size: 18px; white-space: nowrap; }
  .token-group { display: flex; align-items: center; gap: 8px; margin-left: auto; }
  .token-group input { width: 260px; padding: 6px 10px; border: 1px solid var(--border);
                       border-radius: var(--radius); font-size: 13px; }
  .status-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--danger); flex-shrink: 0; }
  .status-dot.connected { background: var(--success); }

  /* Layout */
  .container { display: grid; grid-template-columns: 300px 1fr; gap: 16px;
               padding: 16px 24px; max-width: 1400px; margin: 0 auto; min-height: calc(100vh - 56px); }
  @media (max-width: 900px) { .container { grid-template-columns: 1fr; } }

  /* Cards */
  .card { background: var(--card); border: 1px solid var(--border);
          border-radius: var(--radius); padding: 16px; }
  .card h2 { font-size: 15px; margin-bottom: 12px; color: var(--text); display: flex;
             align-items: center; justify-content: space-between; }
  .sidebar { display: flex; flex-direction: column; gap: 16px; }

  /* Buttons */
  .btn { padding: 6px 14px; border: none; border-radius: var(--radius); cursor: pointer;
         font-size: 13px; font-weight: 500; transition: background .15s; }
  .btn-primary { background: var(--primary); color: #fff; }
  .btn-primary:hover { background: var(--primary-hover); }
  .btn-danger { background: var(--danger); color: #fff; }
  .btn-danger:hover { background: var(--danger-hover); }
  .btn-sm { padding: 3px 10px; font-size: 12px; }
  .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
  .btn-outline:hover { background: var(--bg); }
  .btn:disabled { opacity: .5; cursor: not-allowed; }

  /* Select / Input */
  select, input[type=text], input[type=number], textarea {
    width: 100%; padding: 6px 10px; border: 1px solid var(--border);
    border-radius: var(--radius); font-size: 13px; background: #fff; }
  textarea { resize: vertical; min-height: 50px; font-family: monospace; }
  label { font-size: 13px; font-weight: 500; color: var(--text-light); display: block; margin-bottom: 3px; }

  /* Table */
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }
  th { background: var(--bg); font-weight: 600; color: var(--text-light); position: sticky; top: 0; }
  tr:hover td { background: #f8fafc; }

  /* GPU stock table */
  .stock-table td:nth-child(2), .stock-table td:nth-child(3) { text-align: right; }
  .stock-table th:nth-child(2), .stock-table th:nth-child(3) { text-align: right; }

  /* Status badge */
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .badge-running { background: #dcfce7; color: #166534; }
  .badge-stopped, .badge-offline { background: #f1f5f9; color: #475569; }
  .badge-pending, .badge-waiting { background: #fef3c7; color: #92400e; }
  .badge-failed, .badge-error { background: #fee2e2; color: #991b1b; }

  /* Form grid */
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .form-grid .full { grid-column: 1 / -1; }
  .form-actions { margin-top: 12px; display: flex; gap: 8px; }

  /* Image list */
  .image-list { max-height: 160px; overflow-y: auto; font-size: 13px; }
  .image-item { padding: 4px 0; border-bottom: 1px solid var(--border); color: var(--text-light);
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Toast */
  .toast-container { position: fixed; top: 16px; right: 16px; z-index: 100; display: flex;
                     flex-direction: column; gap: 8px; }
  .toast { padding: 10px 16px; border-radius: var(--radius); color: #fff; font-size: 13px;
           animation: fadeIn .2s; max-width: 360px; word-break: break-all; }
  .toast-success { background: var(--success); }
  .toast-error { background: var(--danger); }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }

  /* Op buttons in table */
  .op-btns { display: flex; gap: 4px; white-space: nowrap; }

  /* Loading */
  .loading { color: var(--text-light); font-size: 13px; padding: 12px 0; text-align: center; }
</style>
</head>
<body>

<div class="header">
  <h1>HQ Job Manager</h1>
  <div class="token-group">
    <div class="status-dot" id="statusDot"></div>
    <input type="text" id="tokenInput" placeholder="API Token">
    <button class="btn btn-primary btn-sm" onclick="connect()">Connect</button>
  </div>
</div>

<div class="container">
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="card">
      <h2>Region</h2>
      <select id="regionSelect" onchange="loadGpuStock()">
        <option value="">-- connect first --</option>
      </select>
    </div>
    <div class="card">
      <h2>GPU Stock <button class="btn btn-outline btn-sm" onclick="loadGpuStock()">Refresh</button></h2>
      <div id="gpuStockArea"><div class="loading">Not connected</div></div>
    </div>
    <div class="card">
      <h2>Images <button class="btn btn-outline btn-sm" onclick="loadImages()">Refresh</button></h2>
      <div id="imageListArea"><div class="loading">Not connected</div></div>
    </div>
  </div>

  <!-- Main -->
  <div style="display:flex;flex-direction:column;gap:16px;">
    <!-- Submit form -->
    <div class="card">
      <h2>Submit New Task</h2>
      <div class="form-grid">
        <div>
          <label>Name *</label>
          <input type="text" id="f_name" placeholder="my-task">
        </div>
        <div>
          <label>Image</label>
          <select id="f_image"><option value="ml_backend:0.0.1">ml_backend:0.0.1</option></select>
        </div>
        <div>
          <label>Command</label>
          <input type="text" id="f_command" value="python3">
        </div>
        <div>
          <label>GPU Num</label>
          <input type="number" id="f_gpu_num" value="1" min="1" max="8">
        </div>
        <div class="full">
          <label>Args (comma separated)</label>
          <input type="text" id="f_args" placeholder='-c, "print(1)"'>
        </div>
        <div>
          <label>Working Dir</label>
          <input type="text" id="f_working_dir" value="/root/autodl-tmp/">
        </div>
        <div>
          <label>Output Dir</label>
          <input type="text" id="f_output_dir" value="output">
        </div>
        <div>
          <label>Priority</label>
          <input type="number" id="f_priority" value="0">
        </div>
        <div>
          <label>Description</label>
          <input type="text" id="f_description" placeholder="optional">
        </div>
        <div class="full">
          <label>Env (JSON)</label>
          <textarea id="f_env" rows="2" placeholder='{"KEY": "VALUE"}'>{}</textarea>
        </div>
        <div class="full">
          <label>Input Paths (comma separated)</label>
          <input type="text" id="f_input_paths" placeholder="cos://bucket/path1, cos://bucket/path2">
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" id="submitBtn" onclick="submitJob()">Submit Task</button>
      </div>
    </div>

    <!-- Task list -->
    <div class="card" style="flex:1;">
      <h2>Task List <button class="btn btn-outline btn-sm" onclick="loadJobs()">Refresh</button></h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Name</th><th>Status</th><th>Type</th><th>Region</th><th>GPU</th><th>Created</th><th>Actions</th></tr>
          </thead>
          <tbody id="jobsBody">
            <tr><td colspan="7" class="loading">Not connected</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<div class="toast-container" id="toasts"></div>

<script>
let TOKEN = localStorage.getItem('hqjob_token') || '';
let refreshTimer = null;

function el(id) { return document.getElementById(id); }

function toast(msg, type) {
  const d = document.createElement('div');
  d.className = 'toast toast-' + type;
  d.textContent = msg;
  el('toasts').appendChild(d);
  setTimeout(() => d.remove(), 4000);
}

async function api(method, path, body) {
  const opts = { method, headers: { 'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(path, opts);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || resp.statusText);
  }
  return resp.json();
}

function badgeClass(status) {
  const s = (status || '').toLowerCase();
  if (s.includes('running') || s === 'active') return 'badge-running';
  if (s.includes('stop') || s === 'offline' || s === 'completed') return 'badge-stopped';
  if (s.includes('pend') || s.includes('wait') || s === 'scheduling') return 'badge-pending';
  if (s.includes('fail') || s.includes('error')) return 'badge-failed';
  return 'badge-stopped';
}

// --- Connect ---
function connect() {
  TOKEN = el('tokenInput').value.trim();
  if (!TOKEN) { toast('Please enter a token', 'error'); return; }
  localStorage.setItem('hqjob_token', TOKEN);
  el('statusDot').classList.add('connected');
  loadAll();
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(loadJobs, 30000);
  toast('Connected', 'success');
}

function loadAll() {
  loadRegions();
  loadImages();
  loadJobs();
}

// --- Regions ---
async function loadRegions() {
  try {
    const r = await api('GET', '/api/v1/resources/regions');
    const sel = el('regionSelect');
    sel.innerHTML = '';
    const regions = r.data || {};
    for (const [name, sign] of Object.entries(regions)) {
      const opt = document.createElement('option');
      opt.value = sign; opt.textContent = name;
      if (sign === 'chongqingDC1') opt.selected = true;
      sel.appendChild(opt);
    }
    loadGpuStock();
  } catch (e) { toast('Load regions failed: ' + e.message, 'error'); }
}

// --- GPU Stock ---
async function loadGpuStock() {
  const area = el('gpuStockArea');
  const region = el('regionSelect').value;
  if (!region) { area.innerHTML = '<div class="loading">Select a region</div>'; return; }
  area.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const r = await api('GET', '/api/v1/resources/gpu_stock?region=' + region);
    const stocks = r.data || {};
    const keys = Object.keys(stocks);
    if (keys.length === 0) { area.innerHTML = '<div class="loading">No data</div>'; return; }
    let html = '<table class="stock-table"><thead><tr><th>GPU</th><th>Idle</th><th>Total</th></tr></thead><tbody>';
    for (const gpu of keys) {
      const s = stocks[gpu];
      const idle = s.idle_gpu_num, total = s.total_gpu_num;
      const color = idle > 0 ? 'var(--success)' : 'var(--danger)';
      html += '<tr><td>' + gpu + '</td><td style="color:' + color + '">' + idle + '</td><td>' + total + '</td></tr>';
    }
    html += '</tbody></table>';
    area.innerHTML = html;
  } catch (e) { area.innerHTML = '<div class="loading">Error: ' + e.message + '</div>'; }
}

// --- Images ---
async function loadImages() {
  const area = el('imageListArea');
  area.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const r = await api('GET', '/api/v1/resources/images');
    const images = r.data || [];
    if (images.length === 0) { area.innerHTML = '<div class="loading">No images</div>'; return; }
    let html = '<div class="image-list">';
    const sel = el('f_image');
    sel.innerHTML = '';
    for (const img of images) {
      html += '<div class="image-item">' + img.image_name + '</div>';
      const opt = document.createElement('option');
      opt.value = img.image_name; opt.textContent = img.image_name;
      sel.appendChild(opt);
    }
    html += '</div>';
    area.innerHTML = html;
  } catch (e) { area.innerHTML = '<div class="loading">Error: ' + e.message + '</div>'; }
}

// --- Submit Job ---
async function submitJob() {
  const name = el('f_name').value.trim();
  if (!name) { toast('Name is required', 'error'); return; }

  let env = {};
  try { env = JSON.parse(el('f_env').value || '{}'); } catch { toast('Env must be valid JSON', 'error'); return; }

  const argsRaw = el('f_args').value.trim();
  const args = argsRaw ? argsRaw.split(',').map(s => s.trim()).filter(Boolean) : [];
  const inputRaw = el('f_input_paths').value.trim();
  const input_paths = inputRaw ? inputRaw.split(',').map(s => s.trim()).filter(Boolean) : [];

  const body = {
    name,
    command: el('f_command').value.trim() || 'python3',
    args,
    working_dir: el('f_working_dir').value.trim(),
    output_dir: el('f_output_dir').value.trim(),
    env,
    priority: parseInt(el('f_priority').value) || 0,
    description: el('f_description').value.trim(),
    input_paths,
    image: el('f_image').value,
    gpu_num: parseInt(el('f_gpu_num').value) || 1,
  };

  el('submitBtn').disabled = true;
  try {
    const r = await api('POST', '/api/v1/jobs', body);
    toast('Task submitted: ' + (r.data?.job_uuid || 'ok'), 'success');
    el('f_name').value = '';
    el('f_description').value = '';
    loadJobs();
  } catch (e) { toast('Submit failed: ' + e.message, 'error'); }
  el('submitBtn').disabled = false;
}

// --- Jobs List ---
async function loadJobs() {
  const tbody = el('jobsBody');
  try {
    const r = await api('GET', '/api/v1/jobs');
    const jobs = r.data || [];
    if (jobs.length === 0) { tbody.innerHTML = '<tr><td colspan="7" class="loading">No tasks</td></tr>'; return; }
    let html = '';
    for (const j of jobs) {
      const t = j.created_at ? new Date(j.created_at).toLocaleString() : '';
      html += '<tr>'
        + '<td title="' + j.uuid + '">' + j.name + '</td>'
        + '<td><span class="badge ' + badgeClass(j.status) + '">' + j.status + '</span></td>'
        + '<td>' + j.deployment_type + '</td>'
        + '<td>' + j.region_sign + '</td>'
        + '<td>' + (j.gpu_name_set || []).join(', ') + '</td>'
        + '<td>' + t + '</td>'
        + '<td class="op-btns">'
        + '<button class="btn btn-outline btn-sm" onclick="stopJob(\\'' + j.uuid + '\\')">Stop</button>'
        + '<button class="btn btn-danger btn-sm" onclick="deleteJob(\\'' + j.uuid + '\\')">Delete</button>'
        + '</td></tr>';
    }
    tbody.innerHTML = html;
  } catch (e) { tbody.innerHTML = '<tr><td colspan="7" class="loading">Error: ' + e.message + '</td></tr>'; }
}

async function stopJob(uuid) {
  if (!confirm('Stop this task?')) return;
  try {
    await api('POST', '/api/v1/jobs/' + uuid + '/stop');
    toast('Stop signal sent', 'success');
    loadJobs();
  } catch (e) { toast('Stop failed: ' + e.message, 'error'); }
}

async function deleteJob(uuid) {
  if (!confirm('Delete this task? This cannot be undone.')) return;
  try {
    await api('DELETE', '/api/v1/jobs/' + uuid);
    toast('Task deleted', 'success');
    loadJobs();
  } catch (e) { toast('Delete failed: ' + e.message, 'error'); }
}

// --- Init ---
window.addEventListener('DOMContentLoaded', () => {
  if (TOKEN) {
    el('tokenInput').value = TOKEN;
    el('statusDot').classList.add('connected');
    loadAll();
    refreshTimer = setInterval(loadJobs, 30000);
  }
});
</script>
</body>
</html>"""

