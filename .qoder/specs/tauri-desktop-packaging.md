# Tauri 桌面版打包方案

## 概述
将 HQ Job Web UI 打包为跨平台桌面应用。Tauri v2 作为外壳，PyInstaller 将 Python 后端打包为单文件 exe，Tauri 以 sidecar 方式管理后端进程。首次运行显示设置页面配置 Token。

## 架构

```
Tauri Desktop App
  ├── WebView → 加载 http://127.0.0.1:{PORT}/ui
  ├── Rust Core → 管理 sidecar 进程、读写配置
  └── Sidecar (hq_job_server.exe) → PyInstaller 打包的 FastAPI 后端
```

启动流程：
1. Tauri 启动 → 读取 `config.json`
2. 首次运行(无配置) → 显示设置页面让用户填写 AUTODL_TOKEN 等
3. 有配置 → 检测可用端口 → 以环境变量方式传参启动 sidecar exe
4. 健康检查轮询 `GET /health`（每 500ms，最多 30s）
5. 后端就绪 → WebView 导航到 `http://127.0.0.1:{PORT}/ui`
6. 窗口关闭 → kill sidecar 进程

## 目录结构

```
e:\dev\ai\hq_job\
├── hq_job/                          # 现有 Python 包
├── pyproject.toml                   # 现有
├── hq_job_server_entry.py           # 新建：PyInstaller 入口
├── hq_job.spec                      # 新建：PyInstaller spec
│
└── desktop/                         # 新建：Tauri 项目
    ├── package.json                 # npm + @tauri-apps/cli
    ├── src/
    │   └── index.html               # 加载页 + 设置页
    ├── src-tauri/
    │   ├── Cargo.toml
    │   ├── tauri.conf.json
    │   ├── capabilities/default.json
    │   ├── binaries/                # sidecar exe 放这里
    │   ├── icons/
    │   └── src/
    │       ├── main.rs              # 入口：注册 commands、setup 钩子
    │       ├── sidecar.rs           # sidecar 启停、端口探测、健康检查
    │       ├── config.rs            # config.json 读写
    │       └── commands.rs          # IPC: get_config, save_config, get_server_url, restart_backend
    └── scripts/
        └── build.js                 # 构建编排：PyInstaller → rename → tauri build
```

## 修改现有文件

### `hq_job/server.py`
- lifespan 中 `AUTODL_TOKEN` 为空时改为 warning 而非 `raise RuntimeError`，使健康检查能通过

### `hq_job/web_ui.py`
- Header 增加 Settings 按钮（仅 Tauri 环境可见，~5 行 JS 检测 `window.__TAURI__`）

## 新建文件详情

### `hq_job_server_entry.py`
```python
from hq_job.server import main
main()
```

### `hq_job.spec` (PyInstaller)
- 入口：`hq_job_server_entry.py`
- onefile 模式
- Hidden imports: uvicorn 子模块、fastapi、anyio、paramiko.transport、cryptography 等
- 输出：`dist/hq_job_server[.exe]`

### `desktop/src-tauri/tauri.conf.json` 关键配置
- `identifier`: `com.hqjob.desktop`
- `windows[0]`: 1280x800, title "HQ Job Manager"
- `bundle.externalBin`: `["binaries/hq_job_server"]`
- CSP: 允许 `http://localhost:*` 和 `https://cdn.jsdelivr.net`
- 生产 `frontendDist`: `../src`；开发 `devUrl`: `http://localhost:9090/ui`

### `desktop/src-tauri/src/sidecar.rs` 核心逻辑
1. 端口检测：尝试 bind config.port → 失败则 bind 0 获取系统分配端口
2. spawn sidecar：`Command::new_sidecar("hq_job_server").env(...)` 传入 TOKEN/PORT
3. `SERVER_HOST` 强制 `127.0.0.1`（安全：仅本机访问）
4. 健康检查循环：500ms 间隔 poll `/health`
5. 成功后 emit `backend-ready` 事件给前端
6. 窗口关闭时 kill child process

### `desktop/src/index.html`
- 状态 1（加载中）：显示 "正在启动后端服务..." 动画
- 状态 2（无配置）：显示设置表单（AUTODL_TOKEN、API_TOKEN、COS_PREFIX、PORT）
- 状态 3（后端就绪）：`window.location.href = serverUrl + '/ui'`
- 调用 Tauri IPC: `invoke('get_config')`, `invoke('save_config', {...})`, `invoke('get_server_url')`
- 监听 `backend-ready` 事件触发跳转

## 构建流程

```
1. pip install pyinstaller
2. pyinstaller hq_job.spec --clean
3. rustc --print host-triple → 获取平台三元组
4. cp dist/hq_job_server → desktop/src-tauri/binaries/hq_job_server-{triple}
5. cd desktop && npm run tauri build
6. 产物在 desktop/src-tauri/target/release/bundle/
```

## 验证步骤
1. 运行 PyInstaller 构建，验证 `dist/hq_job_server.exe` 可独立启动
2. 设置环境变量后运行 exe，验证 `/health` 和 `/ui` 正常
3. 运行 `tauri dev`，验证窗口启动 → 显示加载页 → 跳转到 /ui
4. 测试设置页面：保存配置 → 重启后端 → 自动跳转
5. 运行 `tauri build`，验证安装包可正常安装和使用
6. 测试端口冲突场景：占用 9090 端口后启动应用，验证自动切换端口
