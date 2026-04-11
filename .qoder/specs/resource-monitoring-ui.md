# Resource Monitoring UI - Implementation Plan

## Overview
Add resource monitoring to the Task List in web UI. Running tasks get a "Monitor" button; clicking it expands a row below showing CPU, GPU, Memory, and Disk usage with progress bars. Disk >90% shown in red.

## Files to Modify
- `hq_job/server.py` - New API endpoint + SSH command execution + output parsing
- `hq_job/web_ui.py` - CSS, Monitor button, expandable row JS logic

---

## Step 1: Backend - `server.py`

### 1.1 New helper: `_run_monitor_command(host, port, user, password)`
- Uses `paramiko.SSHClient` + `exec_command` (NOT `invoke_shell`)
- Runs a single combined shell command collecting all metrics:
  ```
  echo "===CPU===" && top -bn1 | grep '%Cpu' &&
  echo "===GPU===" && nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null ;
  echo "===MEM===" && free -b | grep Mem ;
  echo "===DISK===" && df -B1 /root/autodl-tmp/ 2>/dev/null | tail -1 ; df -B1 / | tail -1
  ```
- Runs in `loop.run_in_executor()` to avoid blocking the event loop
- SSH connect timeout=10s, command timeout=15s

### 1.2 New helper: `_parse_monitor_output(raw: str) -> dict`
Splits output by `===SECTION===` markers and parses each:
- **CPU**: Extract idle% from `top` output via regex `(\d+[\.,]\d+)\s*id`, usage = 100 - idle
- **GPU**: Parse CSV lines -> list of `{index, name, util_pct, mem_used_mib, mem_total_mib, mem_pct, temp_c}`; empty list if nvidia-smi missing
- **Memory**: Parse `free -b` output -> `{total_bytes, used_bytes, usage_pct}` (use `available` column)
- **Disk**: Parse `df -B1` lines -> list of `{mountpoint, total_bytes, used_bytes, usage_pct, is_critical}` where `is_critical = usage_pct > 90`

### 1.3 New endpoint: `GET /api/v1/jobs/{job_uuid}/monitor`
1. Get container via `container_list(job_uuid, status=["running"])`; 404 if none
2. Parse SSH credentials with `_parse_ssh_command()`
3. Call `_run_monitor_command()` in executor
4. Parse output with `_parse_monitor_output()`
5. Return `ApiResponse(data={cpu, gpu, memory, disks})`

Error handling:
- SSH failure -> 503
- No running container -> 404
- Parse failure per field -> that field returns null, others still returned

---

## Step 2: Frontend - `web_ui.py`

### 2.1 CSS additions
- `.btn-monitor` / `.btn-monitor.active` - Monitor button style (primary color outline)
- `.monitor-row td` - Expanded row background `#f8fafc`
- `.monitor-grid` - Grid layout for metrics (2 columns on desktop)
- `.progress-block` - Container for label + bar + value
- `.progress-bar-wrap` - 8px height bar background
- `.progress-bar-fill` - Fill with transition animation, blue by default
- `.progress-bar-fill.critical` - Red fill for disk >90%

### 2.2 JS: State management
```javascript
const monitorStates = {};  // uuid -> { timer, isOpen }
```

### 2.3 JS: `toggleMonitor(uuid)`
- If open: clear timer, remove monitor row, delete state
- If closed: insert `<tr class="monitor-row">` after task row, fetch data, start 5s interval

### 2.4 JS: `fetchMonitor(uuid)`
- Call `GET /api/v1/jobs/{uuid}/monitor`
- On success: call `renderMonitorData(uuid, data)`
- On 404: close monitor (container stopped)
- On error: show error in panel, keep retrying

### 2.5 JS: `renderMonitorData(uuid, data)`
Build HTML with progress bars:
- CPU: single bar
- GPU: per-GPU block with utilization bar + VRAM bar + temperature
- Memory: single bar with GB values
- Disk: per-mountpoint bar, `.critical` class if `is_critical`

### 2.6 JS: `formatBytes(bytes)` helper
Format bytes to human-readable (MB/GB/TB)

### 2.7 Modify `loadJobs()`
- Add `data-uuid` attribute to each `<tr>`
- Add Monitor button for running tasks (next to SSH)
- After re-rendering tbody, re-insert open monitor rows and re-fetch data

---

## Verification
1. Start server: ensure no import errors
2. With a running task, click Monitor button -> should see expanding row with resource data
3. Verify disk >90% shows red progress bar
4. Verify auto-refresh updates data every 5 seconds
5. Verify closing (toggle) stops polling
6. Verify loadJobs refresh preserves open monitor rows
7. Test with stopped task -> should not show Monitor button
