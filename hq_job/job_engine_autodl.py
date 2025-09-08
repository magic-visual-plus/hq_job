
from .job_engine import JobDescription, JobEngine
from hq_job.autodl_client import AutodlClient
import base64


class JobEngineAutodl(JobEngine):
    """
    Job Engine for AutoDL jobs.
    This engine is designed to handle AutoDL specific job execution and management.
    """
    
    def __init__(self, token: str):
        super().__init__()
        self.autodl_client = AutodlClient(token=token)
        pass

    def run(self, job: JobDescription) -> int:
        image_uuid = self.autodl_client.image_name2uuid(job.image)
        env = job.to_env()
        self.autodl_client.create_job_deployment(
            name=job.name,
            image_uuid=image_uuid,
            cmd=JobEngineAutodl.default_command(),
            gpu_num=job.gpu_num,
            env_vars=env,
        )

        # run the job
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

    @classmethod
    def default_command(cls, job_desc: JobDescription) -> str:
        job_json = job_desc.to_json()
        job_code = base64.b64encode(job_json.encode('utf-8')).decode('utf-8')
        cmd = f"python3 -m hq_job.scripts.job_worker_entry_autodl '{job_code}' > job.log 2>&1 ; coscmd upload job.log ml_backend/${{AutoDLContainerUUID}}/"
        return cmd