import os
from typing import Optional
from contextlib import asynccontextmanager

import loguru
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse

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
        raise RuntimeError("AUTODL_TOKEN environment variable is required")
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
        deployments = engine.list(name=name)
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
