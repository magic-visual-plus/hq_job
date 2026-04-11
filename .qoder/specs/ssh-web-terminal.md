# SSH Web Terminal Implementation Plan

## Overview
在 HQ Job Web UI 的任务列表中，为 running 状态的任务增加 "SSH" 按钮，点击后在浏览器内打开 xterm.js 交互式终端，通过 WebSocket + paramiko 连接到 AutoDL 容器。

## Files to Modify
- `hq_job/server.py` - 新增 REST API + WebSocket 端点
- `hq_job/web_ui.py` - 新增前端 SSH 终端 UI 和逻辑

## Architecture

```
xterm.js (browser) <--WebSocket--> FastAPI (server.py) <--paramiko SSH--> AutoDL Container
```

---

## Step 1: server.py - 新增 REST API 获取容器 SSH 信息

新增 `GET /api/v1/jobs/{job_uuid}/ssh` 端点：
- 调用 `engine.autodl_client.container_list(job_uuid, status=["running"])` 获取运行中容器
- 无容器返回 404
- 取第一个容器，用 `parse_ssh_command` 解析 `container.info.ssh_command`
- 返回 `{ container_uuid, host, port, username }`（不返回密码）

新增 import:
```python
import asyncio
import json
import paramiko
from fastapi import WebSocket, WebSocketDisconnect, Query as WsQuery
```

复用 `job_engine_autodl.py` 中的 `parse_ssh_command` 逻辑（内联到 handler 中或调用 engine 方法）。

## Step 2: server.py - 新增 WebSocket 端点

新增 `WebSocket /api/v1/jobs/{job_uuid}/ssh/ws?token=xxx`：

1. **认证**: 从 query param 获取 token，与 `API_TOKEN` 比对，不匹配则 close(1008)
2. **获取 SSH 信息**: 调用 `container_list` 获取容器，解析 SSH 凭据
3. **建立 SSH 连接**: 在 `run_in_executor` 中用 paramiko 连接
   ```python
   ssh = paramiko.SSHClient()
   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   ssh.connect(host, port=port, username=user, password=password)
   channel = ssh.invoke_shell(term='xterm-256color', width=80, height=24)
   ```
4. **双向转发** (两个 asyncio Task):
   - **SSH -> WS**: `channel.recv(4096)` 在 executor 中运行，`ws.send_bytes(data)` 发给前端
   - **WS -> SSH**: `ws.receive_text()` 接收前端输入，尝试 JSON 解析判断是否为 resize 控制帧，否则 `channel.send(data)`
5. **清理**: finally 中关闭 channel 和 ssh_client

## Step 3: web_ui.py - CDN 引入 xterm.js

在 `<head>` 中 `</style>` 后、`</head>` 前添加：
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css">
<script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@xterm/addon-fit@0.10.0/lib/addon-fit.js"></script>
```

## Step 4: web_ui.py - 新增 CSS 样式

在现有 `</style>` 前添加 SSH 模态框样式：
- `.ssh-modal-overlay` - 全屏遮罩 (fixed, z-index: 200)
- `.ssh-modal` - 终端容器卡片 (900px, 深色背景)
- `.ssh-modal-header` - 标题栏 + 关闭按钮
- `.ssh-modal-body` - xterm.js 挂载区域
- `.btn-ssh` - SSH 按钮 (绿色 outline 风格)

## Step 5: web_ui.py - 新增 SSH 模态框 HTML

在 `<div class="toast-container">` 之前插入：
```html
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
```

## Step 6: web_ui.py - 修改 loadJobs() 添加 SSH 按钮

在 `loadJobs()` 函数中，Actions 列的 Stop/Delete 按钮之前，添加 SSH 按钮（仅 running 状态）：
```javascript
const isRunning = (j.status || '').toLowerCase().includes('running');
// 在 Actions td 中追加:
+ (isRunning ? '<button class="btn btn-sm btn-ssh" onclick="openSsh(\\''+j.uuid+'\\',\\''+j.name+'\\')">SSH</button>' : '')
```

表格 colspan 从 7 更新（如有需要）。

## Step 7: web_ui.py - 新增 JS 函数

全局变量：
```javascript
let sshTerm = null;
let sshWs = null;
let sshFitAddon = null;
```

### `openSsh(uuid, name)`:
1. 调用 `api('GET', '/api/v1/jobs/' + uuid + '/ssh')` 获取容器信息
2. 显示模态框，设置标题
3. 销毁旧的 term/ws（如果有）
4. 创建 `new Terminal({ cursorBlink: true, fontSize: 14, fontFamily: 'Consolas, monospace', theme: { background: '#000' } })`
5. 创建 FitAddon，加载并挂载到 `#sshTerminal`
6. `requestAnimationFrame(() => fitAddon.fit())`
7. 建立 WebSocket: `ws://host/api/v1/jobs/{uuid}/ssh/ws?token=xxx`
8. `ws.binaryType = 'arraybuffer'`
9. `ws.onopen`: 发送 resize 帧 `{type:'resize', cols, rows}`
10. `ws.onmessage`: `term.write(new Uint8Array(ev.data))`
11. `ws.onclose/onerror`: 终端显示红色 `[Connection closed]`
12. `term.onData(data => ws.send(data))`: 转发用户输入
13. 监听 `term.onResize` 发送 resize 帧

### `closeSshModal()`:
1. 隐藏模态框
2. 关闭 WebSocket
3. `term.dispose()` 清理

### resize 处理:
- 窗口 resize 时调用 `fitAddon.fit()`，防抖 300ms
- `term.onResize` 回调发送 `{type:'resize', cols, rows}` 给 WebSocket

---

## Verification

1. 启动服务: `python -m hq_job.server`
2. 访问 `/ui`，连接后查看任务列表
3. 确认 running 状态任务的 Actions 列有 "SSH" 按钮
4. 点击 SSH 按钮，确认模态框弹出、xterm.js 终端渲染
5. 确认能在终端中执行命令（ls、pwd 等）
6. 测试终端窗口大小调整
7. 测试关闭模态框后 WebSocket 断开
8. 测试非 running 状态任务无 SSH 按钮
