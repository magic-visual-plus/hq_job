# FastAPI Task Management Service

## Overview
Wrap `JobEngineAutodl` with a FastAPI HTTP service, providing task CRUD operations with simple Token authentication.

## Files to Modify/Create

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | Modify | Add `fastapi`, `uvicorn[standard]` dependencies |
| `hq_job/server.py` | Create | FastAPI app, routes, auth, models, config, entry point |

Keep it all in one file - the service is simple enough (5 endpoints + health check).

## Configuration (Environment Variables)

| Env Var | Required | Description |
|---------|----------|-------------|
| `AUTODL_TOKEN` | Yes | AutoDL API token for `JobEngineAutodl` |
| `API_TOKEN` | Yes | Token to protect the HTTP service |
| `SERVER_HOST` | No | Listen address, default `0.0.0.0` |
| `SERVER_PORT` | No | Listen port, default `9090` |

## API Endpoints

Base path: `/api/v1`

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Health check | No |
| POST | `/api/v1/jobs` | Submit a new job | Yes |
| GET | `/api/v1/jobs` | List all jobs (optional `?name=` filter) | Yes |
| GET | `/api/v1/jobs/{job_uuid}/status` | Get job status | Yes |
| POST | `/api/v1/jobs/{job_uuid}/stop` | Stop a job | Yes |
| DELETE | `/api/v1/jobs/{job_uuid}` | Delete a job | Yes |

## Authentication

- Header: `Authorization: Bearer <API_TOKEN>`
- Implemented as a FastAPI `Depends` function
- Returns 401 on missing/invalid token

## Request/Response Models (Pydantic)

### JobSubmitRequest
```python
class JobSubmitRequest(BaseModel):
    name: str
    command: str = "python3"
    args: List[str] = ["-c", "\"print('Hello World')\""]
    working_dir: str = "/root/autodl-tmp/"
    output_dir: str = "output"
    env: Dict[str, str] = {}
    priority: int = 0
    description: str = ""
    input_paths: List[str] = []
    image: str = "ml_backend:0.0.1"
    gpu_num: int = 1
```

### Response Models
- `JobSubmitResponse`: job_uuid, message
- `JobStatusResponse`: job_uuid, status
- `JobListResponse`: jobs list (mapped from AutodlDeployment)
- `OperationResponse`: success, message
- All wrapped in standard `{"code": 0, "data": ..., "message": "ok"}` format

## Error Handling

- `AutodlNetworkError` -> 502 Bad Gateway
- Job not found -> 404
- Auth failure -> 401
- Validation errors -> 422 (FastAPI built-in)
- Other exceptions -> 500

Use FastAPI exception handlers for `AutodlNetworkError`.

## Engine Instance

- Create a single `JobEngineAutodl` instance on startup via FastAPI `lifespan`
- Store in `app.state` and inject via `Depends`

## Entry Point

```bash
# Via uvicorn
uvicorn hq_job.server:app --host 0.0.0.0 --port 8000

# Via python module
python -m hq_job.server
```

Add `if __name__ == "__main__"` block calling `uvicorn.run()`.

## Implementation Steps

1. Add `fastapi` and `uvicorn[standard]` to `pyproject.toml` dependencies
2. Create `hq_job/server.py` with:
   - Config loading from env vars
   - Pydantic request/response models
   - Auth dependency (`verify_token`)
   - Engine lifespan management
   - 6 route handlers (health + 5 CRUD)
   - Exception handlers
   - `__main__` entry point

## Verification

1. `pip install -e .` to install with new dependencies
2. Set env vars: `AUTODL_TOKEN`, `API_TOKEN`
3. Run `python -m hq_job.server`
4. Test health: `curl http://localhost:8000/health`
5. Test auth rejection: `curl http://localhost:8000/api/v1/jobs` (expect 401)
6. Test with token: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/jobs`
