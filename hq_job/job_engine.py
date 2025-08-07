import os

class JobDescription:
    def __init__(self, command: str, args: list = None, working_dir: str = None, 
                 output_dir: str = None, env: dict = None, priority: int = 0, 
                 description: str = ""):
        self.command = command  # 任务命令
        self.args = args or []  # 任务参数
        self.working_dir = os.path.abspath(working_dir)  # 工作目录
        self.output_dir = output_dir    # 输出目录
        self.env = env or {}  # 环境变量
        self.priority = priority  # 任务优先级
        self.description = description  # 任务描述
        
        # 运行时信息
        self.job_id = None  # 任务ID
        self.start_time = None  # 开始时间
        self.end_time = None  # 结束时间
        self.status = "pending"  # 任务状态
        self.exit_code = None  # 任务退出码
        self.pid = None  # 任务进程ID
        self.error_message = None  # 任务错误信息
        
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in [
            'command', 'args', 'working_dir', 'output_dir', 'env',
            'priority', 'description', 'job_id', 'start_time', 'end_time',
            'status', 'exit_code', 'pid', 'error_message'
        ]}
    
    @classmethod
    def from_dict(cls, data: dict) -> "JobDescription":
        job = cls(
            command=data.get('command', ''),
            args=data.get('args', []),
            working_dir=data.get('working_dir'),
            output_dir=data.get('output_dir'),
            env=data.get('env', {}),
            priority=data.get('priority', 0),
            description=data.get('description', '')
        )
        
        job.job_id = data.get('job_id')
        job.start_time = data.get('start_time')
        job.end_time = data.get('end_time')
        job.status = data.get('status', 'pending')
        job.exit_code = data.get('exit_code')
        job.pid = data.get('pid')
        job.error_message = data.get('error_message')
        
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