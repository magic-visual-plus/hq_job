# Web UI for Task Management

## Overview

在 `hq_job/server.py` 中添加 3 个资源查询 API + 1 个内嵌单页 HTML 路由，实现任务提交、资源展示、任务管理。

## 修改文件

仅修改 `hq_job/server.py`，无需新建文件。

## 新增 API 端点

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/api/v1/resources/regions` | 返回 AutoDL 区域列表 | Yes |
| GET | `/api/v1/resources/gpu_stock?region=xx` | 返回指定区域的 GPU 库存 | Yes |
| GET | `/api/v1/resources/images` | 返回可用镜像列表 | Yes |
| GET | `/ui` | 返回管理页面 HTML | No |

### 端点实现细节

1. **`GET /api/v1/resources/regions`**
   - 直接返回 `AutoDLConstants.REGIONS` 字典 (`{中文名: region_sign}`)
   - 需要 import `AutoDLConstants` from `autodl_client`

2. **`GET /api/v1/resources/gpu_stock`**
   - 接收 `region` query 参数 (默认 `chongqingDC1`)
   - 调用 `engine.autodl_client.gpu_stock_list(region)`
   - 返回 `{gpu_type: {idle_gpu_num, total_gpu_num}}` 格式

3. **`GET /api/v1/resources/images`**
   - 调用 `engine.autodl_client.image_list()`
   - 返回 `[{id, image_name, image_uuid}]`

4. **`GET /ui`**
   - 返回 `HTMLResponse(content=HTML_PAGE)` (纯字符串常量)
   - 不需要认证

## 新增 import

```python
from fastapi.responses import HTMLResponse
from .autodl_client import AutoDLConstants
```

## HTML 页面设计

### 布局

```
┌──────────────────────────────────────────────────────────────┐
│  HQ Job Manager           [API Token: _______] [Connect]     │
├──────────────────┬───────────────────────────────────────────┤
│  Resources       │  Submit New Task                          │
│                  │  name*, command, args, working_dir,        │
│  Region: [v]     │  output_dir, image[v], gpu_num, priority, │
│                  │  description, env(JSON), input_paths       │
│  GPU Stock:      │                          [Submit]          │
│  ┌────────────┐  │───────────────────────────────────────────│
│  │ GPU Idle/T │  │  Task List                   [Refresh]    │
│  │ 4090 5/10  │  │  ┌─────────────────────────────────────┐  │
│  │ A100 2/8   │  │  │ Name | Status | Type | Time | Ops  │  │
│  └────────────┘  │  │ job1 | running| Job  | ...  |[S][D]│  │
│                  │  └─────────────────────────────────────┘  │
│  Images:         │                                            │
│  - ml_backend    │                                            │
│  - my_image      │                                            │
└──────────────────┴───────────────────────────────────────────┘
```

### 交互流程

1. 用户输入 API Token -> 点击 Connect -> Token 保存到 localStorage
2. 连接后自动加载：区域列表、GPU 库存、镜像列表、任务列表
3. 切换区域 -> 刷新 GPU 库存
4. 提交任务 -> 调用 POST /api/v1/jobs -> 刷新任务列表
5. 停止/删除 -> confirm 后调用对应 API -> 刷新列表
6. 每 30 秒自动刷新任务列表

### 技术方案

- 纯 inline HTML/CSS/JS，作为 Python 字符串常量 `HTML_PAGE`
- 使用 CSS Grid 布局，现代简洁风格
- vanilla JS fetch API 调用后端，Header 带 `Authorization: Bearer <token>`
- 任务状态颜色：running=绿, stopped=灰, pending=黄, failed=红
- Toast 通知显示操作结果

## 实现步骤

1. 在 server.py 顶部添加 `HTMLResponse` 和 `AutoDLConstants` import
2. 在现有路由之后添加 3 个 resource API 端点
3. 编写 `HTML_PAGE` 字符串常量（含完整 HTML/CSS/JS）
4. 添加 `GET /ui` 路由返回 HTML 页面
5. 启动验证

## 验证方案

1. 启动服务 `python -m hq_job.server`
2. 浏览器访问 `http://localhost:8000/ui` 确认页面加载
3. 输入 API Token 点击 Connect
4. 验证区域下拉框加载
5. 验证 GPU 库存表格展示
6. 验证镜像列表展示
7. 填写表单提交任务
8. 验证任务列表展示、停止、删除功能
