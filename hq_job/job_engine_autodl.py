
from .job_engine import JobDescription, JobEngine


class JobEngineAutodl(JobEngine):
    """
    Job Engine for AutoDL jobs.
    This engine is designed to handle AutoDL specific job execution and management.
    """

    def __init__(self,):
        super().__init__()
        pass

    def run(self, job: JobDescription) -> int:
        # check resources

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