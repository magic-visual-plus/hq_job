
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
        job_uuid = self.autodl_client.create_job_deployment(
            name=job.name,
            image_uuid=image_uuid,
            cmd=JobEngineAutodl.default_command(job),
            gpu_num=job.gpu_num,
        )

        return job_uuid
        pass

    def execute(self, job_id: int, command: str):
        pass

    def stop(self, job_id: int):
        pass

    def status(self, job_id: str) -> str:
        return self.autodl_client.deployment_status(job_id)

    def list(self,):
        pass

    def remove(self, job_id: int):
        pass
    
    def log(self, job_id: int):
        pass

    def get_job_output_url(self, job_uuid: str) -> str:
        events = self.autodl_client.container_event_list(job_uuid)
        if not events:
            return ""
        last_event = events[0]
        container_uuid = last_event.deployment_container_uuid
        return JobEngineAutodl.default_output_path(container_uuid)
    
    @classmethod
    def default_command(cls, job_desc: JobDescription) -> str:
        job_json = job_desc.to_json()
        job_code = base64.b64encode(job_json.encode('utf-8')).decode('utf-8')
        output_path = cls.default_output_path('${AutoDLContainerUUID}')
        output_path = output_path[len("cos://"):]
        cmd = f"python3 -m hq_job.scripts.job_worker_entry_autodl '{job_code}' > job.log 2>&1 ; coscmd upload job.log {output_path}"
        return cmd
    
    @classmethod
    def default_output_path(cls, container_uuid: str) -> str:
        return f"cos://ml_backend/autodl/output/{container_uuid}/"