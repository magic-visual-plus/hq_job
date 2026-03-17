from typing import Dict, List
from pydantic import BaseModel


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


class JobInfo(BaseModel):
    uuid: str
    name: str
    status: str
    deployment_type: str
    region_sign: str
    dc_list: List[str]
    gpu_name_set: List[str]
    created_at: str


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: object = None
