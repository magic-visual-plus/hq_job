import os
from typing import Dict
from . import common_utils


class JobDescription:
    def __init__(self, command: str = "python3", args: list = ["-c", "\"print('Hello World')\""],
                 working_dir: str = "working_dir", 
                 output_dir: str = "output", env: dict = dict(), priority: int = 0, 
                 description: str = "", input_paths: list = []):
        self.name = ""  # 任务名称
        self.command = command  # 任务命令
        self.args = args  # 任务参数
        self.working_dir = working_dir  # 工作目录
        self.output_dir = output_dir    # 输出目录
        self.env = env  # 环境变量
        self.priority = priority  # 任务优先级
        self.description = description  # 任务描述
        self.input_paths = input_paths
        
        # 运行时信息
        self.job_id = ""  # 任务ID
        self.start_time = ""  # 开始时间
        self.end_time = ""  # 结束时间
        self.status = "pending"  # 任务状态
        self.exit_code = 0  # 任务退出码
        self.pid = -1  # 任务进程ID
        self.error_message = ""  # 任务错误信息

        # used for autodl
        self.gpu_num = 1
        self.image = "ml_backend_0.0.1"

        self.env_prefix = "HQJOB_"
        
    def to_dict(self, ) -> dict:
        return {k: getattr(self, k) for k in [
            'command', 'args', 'working_dir', 'output_dir', 'env',
            'priority', 'description', 'job_id', 'start_time', 'end_time',
            'status', 'exit_code', 'pid', 'error_message'
        ]}
    
    def to_env(self, ) -> Dict[str, str]:
        env = dict()
        for k, v in self.to_dict().items():
            env_key = f"{self.env_prefix}{k.upper()}"
            env[env_key] = common_utils.to_str(v)
            pass
        return env
    
    @classmethod
    def from_env(cls, env: Dict[str, str]) -> "JobDescription":
        data = dict()
        prefix_len = len("HQJOB_")
        default_ = cls()
        for k, v in env.items():
            if k.startswith("HQJOB_"):
                key = k[prefix_len:].lower()
                target_type = type(getattr(default_, key, str))
                data[key] = common_utils.from_str(v, target_type)
                pass
            pass
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> "JobDescription":
        job = cls()
        for k, v in data.items():
            if hasattr(job, k):
                setattr(job, k, v)
                pass
            pass
        
        return job


class JobEngine(object):

    def __init__(self,):
        pass

    def run(self, job: JobDescription) -> int:
        pass

    def execute(self, job_id: int, command: str):
        pass

    def stop(self, job_id: int):
        pass

    def status(self, job_id: int):
        pass

    def list(self,):
        pass

    def remove(self, job_id: int):
        pass
    
    def log(self, job_id: int):
        pass