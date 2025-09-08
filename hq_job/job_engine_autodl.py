
from .job_engine import JobDescription, JobEngine
from hq_job.autodl_client import AutodlClient


class JobEngineAutodl(JobEngine):
    """
    Job Engine for AutoDL jobs.
    This engine is designed to handle AutoDL specific job execution and management.
    """
    
    def __init__(self,):
        super().__init__()
        self.autodl_client = AutodlClient()
        pass

    def run(self, job: JobDescription) -> int:
        image_id = self.autodl_client.image_name2id(job.image)
        self.autodl_client.create_job_deployment(
            name=job.name,
            image_id=image_id,
            cmd="python3 -m hq_job.scripts.job_worker_entry_autodl > job.log 2>&1 && coscmd upload job.log ml_backend/${AutoDLContainerUUID}/",
            gpu_num=job.gpu_num,
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
    def default_command(cls, ) -> str:
        return "python3 -m hq_job.scripts.job_worker_entry_autodl > job.log 2>&1 && coscmd upload job.log ml_backend/${AutoDLContainerUUID}/"