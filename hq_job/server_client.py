import requests
from typing import Dict, List, Optional

from .server_models import JobSubmitRequest, JobInfo, ApiResponse


class HQJobClientError(Exception):
    """服务端返回非 2xx 或业务码非 0 时抛出"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class HQJobClient:
    """HQ Job Server HTTP 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000", token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> ApiResponse:
        url = f"{self.base_url}{path}"
        resp = requests.request(method, url, headers=self._headers(), **kwargs)
        if resp.status_code >= 400:
            detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            raise HQJobClientError(resp.status_code, str(detail))
        data = resp.json()
        api_resp = ApiResponse(**data)
        if api_resp.code != 0:
            raise HQJobClientError(api_resp.code, api_resp.message)
        return api_resp

    # ------------------------------------------------------------------
    # health
    # ------------------------------------------------------------------

    def health(self) -> dict:
        return self._request("GET", "/health").data

    # ------------------------------------------------------------------
    # jobs
    # ------------------------------------------------------------------

    def submit_job(self, req: JobSubmitRequest) -> str:
        """提交任务，返回 job_uuid"""
        resp = self._request("POST", "/api/v1/jobs", json=req.model_dump())
        return resp.data["job_uuid"]

    def list_jobs(self, name: Optional[str] = None) -> List[JobInfo]:
        """列出任务"""
        params = {}
        if name is not None:
            params["name"] = name
        resp = self._request("GET", "/api/v1/jobs", params=params)
        return [JobInfo(**item) for item in resp.data]

    def get_job_status(self, job_uuid: str) -> str:
        """获取任务状态"""
        resp = self._request("GET", f"/api/v1/jobs/{job_uuid}/status")
        return resp.data["status"]

    def stop_job(self, job_uuid: str) -> None:
        """停止任务"""
        self._request("POST", f"/api/v1/jobs/{job_uuid}/stop")

    def delete_job(self, job_uuid: str) -> None:
        """删除任务"""
        self._request("DELETE", f"/api/v1/jobs/{job_uuid}")

    # ------------------------------------------------------------------
    # resources
    # ------------------------------------------------------------------

    def list_regions(self) -> Dict[str, str]:
        """获取区域列表，返回 {中文名: region_sign}"""
        return self._request("GET", "/api/v1/resources/regions").data

    def get_gpu_stock(self, region: str = "chongqingDC1") -> Dict[str, dict]:
        """获取 GPU 库存，返回 {gpu_type: {idle_gpu_num, total_gpu_num}}"""
        return self._request("GET", "/api/v1/resources/gpu_stock", params={"region": region}).data

    def list_images(self) -> List[dict]:
        """获取镜像列表"""
        return self._request("GET", "/api/v1/resources/images").data
