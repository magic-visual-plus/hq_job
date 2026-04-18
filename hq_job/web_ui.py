
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

  /* SSH modal */
  .ssh-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 200;
                       display: flex; align-items: center; justify-content: center; }
  .ssh-modal { background: #1a1a2e; border-radius: var(--radius); width: 900px; max-width: 95vw;
               overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
  .ssh-modal-header { display: flex; justify-content: space-between; align-items: center;
                      padding: 8px 16px; background: #16213e; color: #e2e8f0; font-size: 14px; }
  .ssh-modal-header button { background: none; border: none; color: #e2e8f0; font-size: 20px;
                             cursor: pointer; padding: 0 4px; line-height: 1; }
  .ssh-modal-header button:hover { color: #fff; }
  .ssh-modal-body { padding: 4px; background: #000; }
  #sshTerminal { height: 480px; }
  .btn-ssh { background: transparent; border: 1px solid var(--success); color: var(--success); }
  .btn-ssh:hover { background: var(--success); color: #fff; }

  /* Monitor button */
  .btn-monitor { background: transparent; border: 1px solid var(--primary); color: var(--primary); }
  .btn-monitor:hover, .btn-monitor.active { background: var(--primary); color: #fff; }

  /* Info button */
  .btn-info { background: transparent; border: 1px solid var(--warning); color: var(--warning); }
  .btn-info:hover { background: var(--warning); color: #fff; }

  /* Credentials modal */
  .cred-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 200;
                        display: flex; align-items: center; justify-content: center; }
  .cred-modal { background: var(--card); border-radius: var(--radius); width: 440px; max-width: 92vw;
                box-shadow: 0 12px 40px rgba(0,0,0,0.25); overflow: hidden; }
  .cred-modal-header { display: flex; justify-content: space-between; align-items: center;
                       padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 15px; font-weight: 600; }
  .cred-modal-header button { background: none; border: none; font-size: 20px; cursor: pointer;
                              color: var(--gray); line-height: 1; }
  .cred-modal-header button:hover { color: var(--text); }
  .cred-modal-body { padding: 16px; }
  .cred-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0;
              border-bottom: 1px solid var(--border); font-size: 13px; }
  .cred-row:last-child { border-bottom: none; }
  .cred-label { font-weight: 600; color: var(--text-light); min-width: 70px; }
  .cred-value { font-family: monospace; color: var(--text); word-break: break-all; flex: 1; margin: 0 10px; }
  .cred-copy { padding: 2px 8px; font-size: 11px; cursor: pointer; background: var(--bg);
               border: 1px solid var(--border); border-radius: 4px; color: var(--text-light); white-space: nowrap; }
  .cred-copy:hover { background: var(--border); }
  .cred-ssh-cmd { margin-top: 12px; padding: 10px; background: var(--bg); border-radius: var(--radius);
                  font-family: monospace; font-size: 12px; color: var(--text); word-break: break-all;
                  display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .cred-ssh-cmd span { flex: 1; }

  /* Monitor expanded row */
  .monitor-row td { background: #f8fafc !important; padding: 12px 16px; }
  .monitor-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px; }
  @media (max-width: 700px) { .monitor-grid { grid-template-columns: 1fr; } }
  .monitor-section-title { font-size: 12px; font-weight: 600; color: var(--text-light); margin-bottom: 4px; }
  .progress-block { margin-bottom: 6px; }
  .progress-label { font-size: 12px; color: var(--text-light); margin-bottom: 2px; display: flex;
                    justify-content: space-between; align-items: center; }
  .progress-bar-wrap { height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
  .progress-bar-fill { height: 100%; border-radius: 4px; transition: width 0.4s ease; background: var(--primary); }
  .progress-bar-fill.critical { background: var(--danger); }
  .progress-bar-fill.warn { background: var(--warning); }
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/css/xterm.css">
<script src="https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@xterm/addon-fit@0.10.0/lib/addon-fit.js"></script>
</head>
<body>

<div class="header">
  <h1>HQ Job Manager</h1>
  <div class="token-group">
    <div class="status-dot" id="statusDot"></div>
    <input type="text" id="tokenInput" placeholder="API Token">
    <button class="btn btn-primary btn-sm" onclick="connect()">Connect</button>
    <button class="btn btn-outline btn-sm" id="settingsBtn" style="display:none" onclick="openSettings()">Settings</button>
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
        <div>
          <label>Region</label>
          <select id="f_region">
            <option value="">-- Auto --</option>
          </select>
        </div>
        <div class="full">
          <label>GPU Types (Ctrl+click to multi-select)</label>
          <select id="f_gpu_types" multiple style="height:80px;">
            <option value="RTX 4090" selected>RTX 4090</option>
            <option value="RTX 4090D">RTX 4090D</option>
            <option value="RTX 4080">RTX 4080</option>
            <option value="RTX 3090">RTX 3090</option>
            <option value="RTX 3080">RTX 3080</option>
            <option value="RTX 3070">RTX 3070</option>
            <option value="RTX 5090">RTX 5090</option>
            <option value="RTX 5090 D">RTX 5090 D</option>
            <option value="RTX PRO 6000">RTX PRO 6000</option>
            <option value="V100">V100</option>
            <option value="A100">A100</option>
            <option value="H100">H100</option>
            <option value="L20">L20</option>
            <option value="L40">L40</option>
          </select>
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

<div id="credModal" class="cred-modal-overlay" style="display:none">
  <div class="cred-modal">
    <div class="cred-modal-header">
      <span id="credModalTitle">Connection Info</span>
      <button onclick="closeCredModal()">&times;</button>
    </div>
    <div class="cred-modal-body" id="credModalBody">
      <div class="loading">Loading...</div>
    </div>
  </div>
</div>

<div id="sshModal" class="ssh-modal-overlay" style="display:none">
  <div class="ssh-modal">
    <div class="ssh-modal-header">
      <span id="sshModalTitle">SSH Terminal</span>
      <button onclick="closeSshModal()">&times;</button>
    </div>
    <div class="ssh-modal-body">
      <div id="sshTerminal"></div>
    </div>
  </div>
</div>

<div class="toast-container" id="toasts"></div>

<script>
let TOKEN = localStorage.getItem('hqjob_token') || '';
let refreshTimer = null;
let regionMap = {};  // sign -> name mapping

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
    const formSel = el('f_region');
    sel.innerHTML = '';
    formSel.innerHTML = '<option value="">-- Auto --</option>';
    regionMap = {};  // reset
    const regions = r.data || {};
    for (const [name, sign] of Object.entries(regions)) {
      regionMap[sign] = name;  // build reverse mapping
      const opt = document.createElement('option');
      opt.value = sign; opt.textContent = name;
      if (sign === 'chongqingDC1') opt.selected = true;
      sel.appendChild(opt);
      
      const formOpt = document.createElement('option');
      formOpt.value = sign; formOpt.textContent = name;
      formSel.appendChild(formOpt);
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

  const gpuSelect = el('f_gpu_types');
  const gpu_name_set = Array.from(gpuSelect.selectedOptions).map(o => o.value);
  const region = el('f_region').value;

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
    gpu_name_set,
    region,
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

// --- Resource Monitor state ---
const monitorStates = {};  // uuid -> { timer, isOpen }

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
      const autodlUrl = 'https://www.autodl.com/deploy/details/' + j.uuid + '/' + j.name;
      const regionNames = (j.dc_list || []).map(dc => regionMap[dc] || dc).join(', ');
      const isRunning = (j.status || '').toLowerCase().includes('running') || (j.status || '').toLowerCase() === 'active';
      const monActive = monitorStates[j.uuid] ? ' active' : '';
      html += '<tr data-uuid="' + j.uuid + '">'
        + '<td title="' + j.uuid + '"><a href="' + autodlUrl + '" target="_blank" style="color:var(--primary);text-decoration:none;">' + j.name + '</a></td>'
        + '<td><span class="badge ' + badgeClass(j.status) + '">' + j.status + '</span></td>'
        + '<td>' + j.deployment_type + '</td>'
        + '<td>' + regionNames + '</td>'
        + '<td>' + (j.gpu_name_set || []).join(', ') + '</td>'
        + '<td>' + t + '</td>'
        + '<td class="op-btns">'
        + (isRunning ? '<button class="btn btn-sm btn-info" onclick="showCredentials(\\'' + j.uuid + '\\',\\'' + j.name + '\\')">Info</button>' : '')
        + (isRunning ? '<button class="btn btn-sm btn-ssh" onclick="openSsh(\\'' + j.uuid + '\\',\\'' + j.name + '\\')">SSH</button>' : '')
        + (isRunning ? '<button id="monitor-btn-' + j.uuid + '" class="btn btn-sm btn-monitor' + monActive + '" onclick="toggleMonitor(\\'' + j.uuid + '\\')">Monitor</button>' : '')
        + '<button class="btn btn-outline btn-sm" onclick="stopJob(\\'' + j.uuid + '\\')">Stop</button>'
        + '<button class="btn btn-danger btn-sm" onclick="deleteJob(\\'' + j.uuid + '\\')">Delete</button>'
        + '</td></tr>';
    }
    tbody.innerHTML = html;
    // Re-insert open monitor rows after refresh
    for (const uuid of Object.keys(monitorStates)) {
      const taskRow = tbody.querySelector('tr[data-uuid="' + uuid + '"]');
      if (taskRow) {
        const mtr = document.createElement('tr');
        mtr.className = 'monitor-row';
        mtr.id = 'monitor-row-' + uuid;
        mtr.innerHTML = '<td colspan="7"><div class="monitor-panel" id="monitor-panel-' + uuid + '"><div class="loading">Loading...</div></div></td>';
        taskRow.insertAdjacentElement('afterend', mtr);
        fetchMonitor(uuid);
      } else {
        // Task row gone (stopped/deleted), clean up
        clearInterval(monitorStates[uuid].timer);
        delete monitorStates[uuid];
      }
    }
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

// --- Resource Monitor ---

function toggleMonitor(uuid) {
  if (monitorStates[uuid]) {
    // Close
    clearInterval(monitorStates[uuid].timer);
    delete monitorStates[uuid];
    const row = document.getElementById('monitor-row-' + uuid);
    if (row) row.remove();
    const btn = document.getElementById('monitor-btn-' + uuid);
    if (btn) btn.classList.remove('active');
  } else {
    // Open
    const taskRow = document.querySelector('tr[data-uuid="' + uuid + '"]');
    if (!taskRow) return;
    const mtr = document.createElement('tr');
    mtr.className = 'monitor-row';
    mtr.id = 'monitor-row-' + uuid;
    mtr.innerHTML = '<td colspan="7"><div class="monitor-panel" id="monitor-panel-' + uuid + '"><div class="loading">Loading...</div></div></td>';
    taskRow.insertAdjacentElement('afterend', mtr);
    const btn = document.getElementById('monitor-btn-' + uuid);
    if (btn) btn.classList.add('active');
    fetchMonitor(uuid);
    const timer = setInterval(() => fetchMonitor(uuid), 15000);
    monitorStates[uuid] = { timer: timer, isOpen: true };
  }
}

async function fetchMonitor(uuid) {
  const panel = document.getElementById('monitor-panel-' + uuid);
  if (!panel) return;
  try {
    const r = await api('GET', '/api/v1/jobs/' + uuid + '/monitor');
    renderMonitorData(uuid, r.data);
  } catch (e) {
    if (e.message && e.message.includes('404')) {
      // Container stopped
      if (monitorStates[uuid]) {
        clearInterval(monitorStates[uuid].timer);
        delete monitorStates[uuid];
      }
      const row = document.getElementById('monitor-row-' + uuid);
      if (row) row.remove();
      const btn = document.getElementById('monitor-btn-' + uuid);
      if (btn) btn.classList.remove('active');
    } else {
      panel.innerHTML = '<div class="loading" style="color:var(--danger)">Error: ' + e.message + '</div>';
    }
  }
}

function formatBytes(bytes) {
  if (bytes == null) return 'N/A';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
  if (bytes < 1099511627776) return (bytes / 1073741824).toFixed(1) + ' GB';
  return (bytes / 1099511627776).toFixed(1) + ' TB';
}

function progressBar(pct, critical) {
  var cls = 'progress-bar-fill';
  if (critical) cls += ' critical';
  else if (pct > 75) cls += ' warn';
  return '<div class="progress-bar-wrap"><div class="' + cls + '" style="width:' + Math.min(pct, 100) + '%"></div></div>';
}

function renderMonitorData(uuid, d) {
  var panel = document.getElementById('monitor-panel-' + uuid);
  if (!panel) return;
  var h = '<div class="monitor-grid">';

  // CPU
  if (d.cpu) {
    h += '<div class="progress-block"><div class="progress-label"><span>CPU</span><span>' + d.cpu.usage_pct + '%</span></div>' + progressBar(d.cpu.usage_pct, false) + '</div>';
  }

  // Memory
  if (d.memory) {
    h += '<div class="progress-block"><div class="progress-label"><span>RAM</span><span>' + formatBytes(d.memory.used_bytes) + ' / ' + formatBytes(d.memory.total_bytes) + ' (' + d.memory.usage_pct + '%)</span></div>' + progressBar(d.memory.usage_pct, false) + '</div>';
  }

  // GPU
  if (d.gpu && d.gpu.length > 0) {
    for (var g of d.gpu) {
      h += '<div class="progress-block"><div class="progress-label"><span>GPU' + g.index + ' ' + g.name + ' ' + g.temp_c + '&#176;C</span><span>' + g.util_pct + '%</span></div>' + progressBar(g.util_pct, false) + '</div>';
      h += '<div class="progress-block"><div class="progress-label"><span>VRAM GPU' + g.index + '</span><span>' + g.mem_used_mib + ' / ' + g.mem_total_mib + ' MiB (' + g.mem_pct + '%)</span></div>' + progressBar(g.mem_pct, false) + '</div>';
    }
  }

  // Disk
  if (d.disks && d.disks.length > 0) {
    for (var dk of d.disks) {
      var diskColor = dk.is_critical ? ' style="color:var(--danger);font-weight:600"' : '';
      h += '<div class="progress-block"><div class="progress-label"><span' + diskColor + '>Disk ' + dk.mountpoint + '</span><span' + diskColor + '>' + formatBytes(dk.used_bytes) + ' / ' + formatBytes(dk.total_bytes) + ' (' + dk.usage_pct + '%)</span></div>' + progressBar(dk.usage_pct, dk.is_critical) + '</div>';
    }
  }

  h += '</div>';
  panel.innerHTML = h;
}

// --- Credentials Info ---
async function showCredentials(uuid, name) {
  el('credModal').style.display = 'flex';
  el('credModalTitle').textContent = 'Connection: ' + name;
  el('credModalBody').innerHTML = '<div class="loading">Loading...</div>';
  try {
    var r = await api('GET', '/api/v1/jobs/' + uuid + '/ssh');
    var d = r.data || {};
    var sshCmd = 'ssh -p ' + d.port + ' ' + d.username + '@' + d.host;
    var html = '';
    html += '<div class="cred-row"><span class="cred-label">Host</span><span class="cred-value">' + (d.host || '') + '</span><button class="cred-copy" onclick="copyText(\\\'' + (d.host || '') + '\\\')">Copy</button></div>';
    html += '<div class="cred-row"><span class="cred-label">Port</span><span class="cred-value">' + (d.port || '') + '</span><button class="cred-copy" onclick="copyText(\\\'' + (d.port || '') + '\\\')">Copy</button></div>';
    html += '<div class="cred-row"><span class="cred-label">Username</span><span class="cred-value">' + (d.username || '') + '</span><button class="cred-copy" onclick="copyText(\\\'' + (d.username || '') + '\\\')">Copy</button></div>';
    html += '<div class="cred-row"><span class="cred-label">Password</span><span class="cred-value">' + (d.password || '') + '</span><button class="cred-copy" onclick="copyText(\\\'' + (d.password || '') + '\\\')">Copy</button></div>';
    html += '<div class="cred-ssh-cmd"><span>' + sshCmd + '</span><button class="cred-copy" onclick="copyText(\\\'' + sshCmd + '\\\')">Copy</button></div>';
    el('credModalBody').innerHTML = html;
  } catch (e) {
    el('credModalBody').innerHTML = '<div class="loading" style="color:var(--danger)">Error: ' + e.message + '</div>';
  }
}

function closeCredModal() {
  el('credModal').style.display = 'none';
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(function() {
    toast('Copied', 'success');
  }).catch(function() {
    toast('Copy failed', 'error');
  });
}

// --- SSH Terminal ---
let sshTerm = null;
let sshWs = null;
let sshFitAddon = null;
let sshResizeTimer = null;
let sshCurrentUuid = null;

async function openSsh(uuid, name) {
  try {
    await api('GET', '/api/v1/jobs/' + uuid + '/ssh');
  } catch (e) {
    toast('SSH not available: ' + e.message, 'error');
    return;
  }

  // Pause monitor polling for this task to avoid SSH resource contention
  if (monitorStates[uuid]) {
    clearInterval(monitorStates[uuid].timer);
    monitorStates[uuid].timer = null;
  }
  sshCurrentUuid = uuid;

  // Show modal
  el('sshModal').style.display = 'flex';
  el('sshModalTitle').textContent = 'SSH: ' + name;

  // Cleanup previous session
  if (sshWs) { try { sshWs.close(); } catch(e){} sshWs = null; }
  if (sshTerm) { try { sshTerm.dispose(); } catch(e){} sshTerm = null; }
  el('sshTerminal').innerHTML = '';

  // Create terminal
  var term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Consolas, "Courier New", monospace',
    theme: { background: '#000000' }
  });
  var fitAddon = new FitAddon.FitAddon();
  term.loadAddon(fitAddon);
  term.open(el('sshTerminal'));
  requestAnimationFrame(function() { fitAddon.fit(); });

  sshTerm = term;
  sshFitAddon = fitAddon;

  // WebSocket
  var proto = location.protocol === 'https:' ? 'wss' : 'ws';
  var wsUrl = proto + '://' + location.host + '/api/v1/jobs/' + uuid + '/ssh/ws?token=' + encodeURIComponent(TOKEN);
  var ws = new WebSocket(wsUrl);
  ws.binaryType = 'arraybuffer';
  sshWs = ws;

  ws.onopen = function() {
    ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }));
  };
  ws.onmessage = function(ev) {
    term.write(new Uint8Array(ev.data));
  };
  ws.onclose = function() {
    term.write('\\r\\n\\x1b[31m[Connection closed]\\x1b[0m\\r\\n');
  };
  ws.onerror = function() {
    term.write('\\r\\n\\x1b[31m[Connection error]\\x1b[0m\\r\\n');
  };

  term.onData(function(data) {
    if (ws.readyState === WebSocket.OPEN) ws.send(data);
  });

  term.onResize(function(size) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'resize', cols: size.cols, rows: size.rows }));
    }
  });
}

function closeSshModal() {
  el('sshModal').style.display = 'none';
  if (sshWs) { try { sshWs.close(); } catch(e){} sshWs = null; }
  if (sshTerm) { try { sshTerm.dispose(); } catch(e){} sshTerm = null; }
  sshFitAddon = null;
  // Resume monitor polling if it was open for this task
  if (sshCurrentUuid && monitorStates[sshCurrentUuid] && !monitorStates[sshCurrentUuid].timer) {
    fetchMonitor(sshCurrentUuid);
    monitorStates[sshCurrentUuid].timer = setInterval(() => fetchMonitor(sshCurrentUuid), 15000);
  }
  sshCurrentUuid = null;
}

// --- Tauri integration ---
function openSettings() {
  if (window.__TAURI__) {
    window.__TAURI__.core.invoke('open_settings');
  }
}

// --- Init ---
window.addEventListener('DOMContentLoaded', () => {
  // Show settings button when running inside Tauri
  if (window.__TAURI__) {
    el('settingsBtn').style.display = '';
  }
  if (TOKEN) {
    el('tokenInput').value = TOKEN;
    el('statusDot').classList.add('connected');
    loadAll();
    refreshTimer = setInterval(loadJobs, 30000);
  }
  // SSH modal: resize terminal on window resize
  window.addEventListener('resize', () => {
    if (sshResizeTimer) clearTimeout(sshResizeTimer);
    sshResizeTimer = setTimeout(() => {
      if (sshFitAddon && sshTerm) sshFitAddon.fit();
    }, 300);
  });
  // Close modals on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (el('sshModal').style.display !== 'none') closeSshModal();
      else if (el('credModal').style.display !== 'none') closeCredModal();
    }
  });
});
</script>
</body>
</html>"""

