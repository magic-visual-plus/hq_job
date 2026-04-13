import os
import re
import asyncio
import json
import time
import traceback
from typing import Optional
from contextlib import asynccontextmanager

import loguru
import paramiko
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse

from .job_engine import JobDescription
from .job_engine_autodl import JobEngineAutodl
from .autodl_client import AutodlNetworkError, AutoDLConstants
from .server_models import JobSubmitRequest, JobInfo, ApiResponse
from .web_ui import HTML_PAGE

logger = loguru.logger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AUTODL_TOKEN = os.environ.get("AUTODL_TOKEN", "")
API_TOKEN = os.environ.get("API_TOKEN", "")
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "9090"))


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not API_TOKEN:
        raise HTTPException(status_code=500, detail="API_TOKEN not configured on server")
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


# ---------------------------------------------------------------------------
# Engine dependency
# ---------------------------------------------------------------------------

def get_engine() -> JobEngineAutodl:
    return app.state.engine


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    if not AUTODL_TOKEN:
        logger.warning("AUTODL_TOKEN not set, AutoDL features will be unavailable")
    if not API_TOKEN:
        logger.warning("API_TOKEN not set, all authenticated endpoints will return 500")
    application.state.engine = JobEngineAutodl(token=AUTODL_TOKEN)
    logger.info(f"Server started on {SERVER_HOST}:{SERVER_PORT}")
    yield
    logger.info("Server shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="HQ Job Server", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(AutodlNetworkError)
async def autodl_error_handler(request, exc: AutodlNetworkError):
    return ApiResponse(code=502, message=f"AutoDL error: {exc.message}", data=None).model_dump()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，打印详细错误信息"""
    error_detail = traceback.format_exc()
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Exception: {type(exc).__name__}: {exc}")
    logger.error(f"Traceback:\n{error_detail}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": str(exc),
            "detail": error_detail
        }
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return ApiResponse(data={"status": "ok"})


@app.post("/api/v1/jobs", dependencies=[Depends(verify_token)])
async def submit_job(
    req: JobSubmitRequest,
    engine: JobEngineAutodl = Depends(get_engine),
):
    job_desc = JobDescription(
        name=req.name,
        command=req.command,
        args=req.args,
        working_dir=req.working_dir,
        output_dir=req.output_dir,
        env=req.env,
        priority=req.priority,
        description=req.description,
        input_paths=req.input_paths,
        image=req.image,
    )
    job_desc.gpu_num = req.gpu_num
    job_desc.gpu_name_set = req.gpu_name_set
    job_desc.region = req.region

    try:
        job_uuid = engine.run(job_desc)
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ApiResponse(data={"job_uuid": job_uuid})


@app.get("/api/v1/jobs", dependencies=[Depends(verify_token)])
async def list_jobs(
    name: Optional[str] = Query(None, description="Filter by job name"),
    engine: JobEngineAutodl = Depends(get_engine),
):
    try:
        deployments = engine.list(name=name, page_size=50, limit=100)
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")

    jobs = [
        JobInfo(
            uuid=d.uuid,
            name=d.name,
            status=d.status,
            deployment_type=d.deployment_type,
            region_sign=d.region_sign,
            dc_list=d.dc_list,
            gpu_name_set=d.gpu_name_set,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in deployments
    ]
    return ApiResponse(data=jobs)


@app.get("/api/v1/jobs/{job_uuid}/status", dependencies=[Depends(verify_token)])
async def get_job_status(
    job_uuid: str,
    engine: JobEngineAutodl = Depends(get_engine),
):
    try:
        status = engine.status(job_uuid)
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")

    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return ApiResponse(data={"job_uuid": job_uuid, "status": status})


@app.post("/api/v1/jobs/{job_uuid}/stop", dependencies=[Depends(verify_token)])
async def stop_job(
    job_uuid: str,
    engine: JobEngineAutodl = Depends(get_engine),
):
    try:
        engine.stop(job_uuid)
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ApiResponse(data={"job_uuid": job_uuid, "message": "stop signal sent"})


@app.delete("/api/v1/jobs/{job_uuid}", dependencies=[Depends(verify_token)])
async def delete_job(
    job_uuid: str,
    engine: JobEngineAutodl = Depends(get_engine),
):
    try:
        engine.remove(job_uuid)
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ApiResponse(data={"job_uuid": job_uuid, "message": "deleted"})


# ---------------------------------------------------------------------------
# Resource routes
# ---------------------------------------------------------------------------

@app.get("/api/v1/resources/regions", dependencies=[Depends(verify_token)])
async def list_regions():
    return ApiResponse(data=AutoDLConstants.REGIONS)


@app.get("/api/v1/resources/gpu_stock", dependencies=[Depends(verify_token)])
async def get_gpu_stock(
    region: str = Query("chongqingDC1", description="Region sign"),
    engine: JobEngineAutodl = Depends(get_engine),
):
    try:
        stocks = engine.autodl_client.gpu_stock_list(region=region)
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")

    data = {
        gpu_type: {"idle_gpu_num": s.idle_gpu_num, "total_gpu_num": s.total_gpu_num}
        for gpu_type, s in stocks.items()
    }
    return ApiResponse(data=data)


@app.get("/api/v1/resources/images", dependencies=[Depends(verify_token)])
async def list_images(
    engine: JobEngineAutodl = Depends(get_engine),
):
    try:
        images = engine.autodl_client.image_list()
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")

    data = [
        {"id": img.id, "image_name": img.image_name, "image_uuid": img.image_uuid}
        for img in images
    ]
    return ApiResponse(data=data)


@app.get("/ui", response_class=HTMLResponse)
async def ui_page():
    return HTML_PAGE


# ---------------------------------------------------------------------------
# SSH routes
# ---------------------------------------------------------------------------

def _parse_ssh_command(ssh_command: str):
    """Parse 'ssh -p port user@host' into (user, host, port)."""
    parts = ssh_command.split()
    if len(parts) != 4:
        raise ValueError(f"Invalid SSH command format: {ssh_command}")
    port = int(parts[2])
    user, host = parts[3].split('@')
    return user, host, port


_MONITOR_CMD = (
    'echo "===CPU===" && top -bn1 | grep "%Cpu" ; '
    'echo "===GPU===" && nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null ; '
    'echo "===MEM===" && free -b | grep Mem ; '
    'echo "===DISK===" && df -B1 /root/autodl-tmp/ 2>/dev/null | tail -1 ; df -B1 / | tail -1'
)


def _run_monitor_command(host: str, port: int, user: str, password: str) -> str:
    """SSH into container and run monitoring command, return raw output."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=port, username=user, password=password, timeout=10,
                    banner_timeout=10, auth_timeout=10)
        _, stdout, stderr = ssh.exec_command(_MONITOR_CMD, timeout=15)
        return stdout.read().decode("utf-8", errors="replace")
    finally:
        ssh.close()


# Monitor data cache: {job_uuid: {"data": dict, "ts": float}}
_monitor_cache: dict = {}
_MONITOR_CACHE_TTL = 10  # seconds


def _parse_monitor_output(raw: str) -> dict:
    """Parse combined monitoring command output into structured data."""
    sections = {}
    current = None
    for line in raw.splitlines():
        if line.startswith("===") and line.endswith("==="):
            current = line.strip("=")
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    result = {"cpu": None, "gpu": [], "memory": None, "disks": []}

    # --- CPU ---
    cpu_lines = sections.get("CPU", [])
    for line in cpu_lines:
        m = re.search(r"([\d.,]+)\s*id", line)
        if m:
            idle = float(m.group(1).replace(",", "."))
            result["cpu"] = {"usage_pct": round(100.0 - idle, 1)}
            break

    # --- GPU ---
    gpu_lines = sections.get("GPU", [])
    for line in gpu_lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 6:
            try:
                mem_used = float(parts[3])
                mem_total = float(parts[4])
                result["gpu"].append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "util_pct": float(parts[2]),
                    "mem_used_mib": mem_used,
                    "mem_total_mib": mem_total,
                    "mem_pct": round(mem_used / mem_total * 100, 1) if mem_total > 0 else 0,
                    "temp_c": int(float(parts[5])),
                })
            except (ValueError, ZeroDivisionError):
                pass

    # --- Memory ---
    mem_lines = sections.get("MEM", [])
    for line in mem_lines:
        parts = line.split()
        if len(parts) >= 7:
            try:
                total = int(parts[1])
                available = int(parts[6])
                used = total - available
                result["memory"] = {
                    "total_bytes": total,
                    "used_bytes": used,
                    "usage_pct": round(used / total * 100, 1) if total > 0 else 0,
                }
            except (ValueError, IndexError):
                pass
            break

    # --- Disk ---
    disk_lines = sections.get("DISK", [])
    seen_mounts = set()
    for line in disk_lines:
        parts = line.split()
        if len(parts) >= 6:
            try:
                mount = parts[5]
                if mount in seen_mounts:
                    continue
                seen_mounts.add(mount)
                total = int(parts[1])
                used = int(parts[2])
                pct = round(used / total * 100, 1) if total > 0 else 0
                result["disks"].append({
                    "mountpoint": mount,
                    "total_bytes": total,
                    "used_bytes": used,
                    "usage_pct": pct,
                    "is_critical": pct > 90,
                })
            except (ValueError, IndexError):
                pass

    return result


@app.get("/api/v1/jobs/{job_uuid}/monitor", dependencies=[Depends(verify_token)])
async def get_job_monitor(
    job_uuid: str,
    engine: JobEngineAutodl = Depends(get_engine),
):
    # Return cached data if fresh enough
    cached = _monitor_cache.get(job_uuid)
    if cached and (time.monotonic() - cached["ts"]) < _MONITOR_CACHE_TTL:
        return ApiResponse(data=cached["data"])

    try:
        containers = engine.autodl_client.container_list(job_uuid, status=["running"])
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")

    if not containers:
        _monitor_cache.pop(job_uuid, None)
        raise HTTPException(status_code=404, detail="No running containers found")

    container = containers[0]
    user, host, port = _parse_ssh_command(container.info.ssh_command)
    password = container.info.root_password

    loop = asyncio.get_event_loop()
    try:
        raw = await loop.run_in_executor(
            None, lambda: _run_monitor_command(host, port, user, password)
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"SSH monitor failed: {e}")

    data = _parse_monitor_output(raw)
    _monitor_cache[job_uuid] = {"data": data, "ts": time.monotonic()}
    return ApiResponse(data=data)


@app.get("/api/v1/jobs/{job_uuid}/ssh", dependencies=[Depends(verify_token)])
async def get_ssh_info(
    job_uuid: str,
    engine: JobEngineAutodl = Depends(get_engine),
):
    try:
        containers = engine.autodl_client.container_list(job_uuid, status=["running"])
    except AutodlNetworkError as e:
        raise HTTPException(status_code=502, detail=f"AutoDL error: {e.message}")

    if not containers:
        raise HTTPException(status_code=404, detail="No running containers found")

    container = containers[0]
    user, host, port = _parse_ssh_command(container.info.ssh_command)
    return ApiResponse(data={
        "container_uuid": container.uuid,
        "host": host,
        "port": port,
        "username": user,
    })


@app.websocket("/api/v1/jobs/{job_uuid}/ssh/ws")
async def ssh_terminal(job_uuid: str, ws: WebSocket, token: str = Query("")):
    # Auth
    if not API_TOKEN or token != API_TOKEN:
        await ws.close(code=1008)
        return

    await ws.accept()

    # Get container SSH info
    engine = get_engine()
    try:
        containers = engine.autodl_client.container_list(job_uuid, status=["running"])
    except Exception as e:
        await ws.send_text(f"\r\nError: {e}\r\n")
        await ws.close()
        return

    if not containers:
        await ws.send_text("\r\nNo running containers found.\r\n")
        await ws.close()
        return

    container = containers[0]
    user, host, port = _parse_ssh_command(container.info.ssh_command)
    password = container.info.root_password

    # Establish SSH connection via paramiko in executor
    loop = asyncio.get_event_loop()
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        await loop.run_in_executor(
            None,
            lambda: ssh_client.connect(host, port=port, username=user, password=password, timeout=10)
        )
        channel = await loop.run_in_executor(
            None,
            lambda: ssh_client.invoke_shell(term='xterm-256color', width=80, height=24)
        )
    except Exception as e:
        await ws.send_text(f"\r\nSSH connection failed: {e}\r\n")
        await ws.close()
        ssh_client.close()
        return

    async def ssh_to_ws():
        """Read from SSH channel and send to WebSocket."""
        try:
            while True:
                data = await loop.run_in_executor(None, lambda: channel.recv(4096))
                if not data:
                    break
                await ws.send_bytes(data)
        except Exception:
            pass

    async def ws_to_ssh():
        """Read from WebSocket and send to SSH channel."""
        try:
            while True:
                data = await ws.receive_text()
                # Check for control frame (resize)
                try:
                    msg = json.loads(data)
                    if isinstance(msg, dict) and msg.get("type") == "resize":
                        cols = int(msg.get("cols", 80))
                        rows = int(msg.get("rows", 24))
                        channel.resize_pty(width=cols, height=rows)
                        continue
                except (json.JSONDecodeError, ValueError):
                    pass
                channel.send(data)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    try:
        task_ssh = asyncio.create_task(ssh_to_ws())
        task_ws = asyncio.create_task(ws_to_ssh())
        done, pending = await asyncio.wait(
            [task_ssh, task_ws], return_when=asyncio.FIRST_COMPLETED
        )
        for t in pending:
            t.cancel()
    finally:
        try:
            channel.close()
        except Exception:
            pass
        try:
            ssh_client.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    uvicorn.run(
        "hq_job.server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
