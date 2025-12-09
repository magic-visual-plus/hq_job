
from .job_engine import JobDescription, JobEngine
from hq_job.autodl_client import AutodlClient, AutodlContainer, AutodlDeployment
import base64
import os
from typing import Tuple
from . import ssh_utils
from . import storage
import loguru
import time
from typing import List

logger = loguru.logger

class JobEngineAutodl(JobEngine):
    """
    Job Engine for AutoDL jobs.
    This engine is designed to handle AutoDL specific job execution and management.
    """
    
    def __init__(self, token: str):
        super().__init__()
        self.autodl_client = AutodlClient(token=token)
        pass

    def run(self, job: JobDescription) -> str:
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

    def stop(self, job_uuid: str):
        containers = self.autodl_client.container_list(job_uuid)
        if containers is None or len(containers) == 0:
            logger.info(f"can't find container for job {job_uuid}, maybe job is finished")
            return
        
        for container in containers:
            if container.status == "running":
                ssh_command = container.info.ssh_command
                password = container.info.root_password
                ssh_user, ssh_host, ssh_port = self.parse_ssh_command(ssh_command)
                ssh_utils.execute_command("pkill -P `cat pid`", host=ssh_host, username=ssh_user, password=password, port=int(ssh_port))
                pass
            pass
        pass

    def status(self, job_id: str) -> str:
        return self.autodl_client.deployment_status(job_id)

    def list(self, name: str = None) -> List[AutodlDeployment]:
        return self.autodl_client.deployment_list(name=name)

    def remove(self, job_uuid: str):
        return self.autodl_client.deployment_delete(job_uuid)
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
    
    def get_job_conainter(self, job_uuid: str) -> AutodlContainer:
        containers = self.autodl_client.container_list(job_uuid)

        if containers is None or len(containers) == 0:
            return None
        elif len(containers) == 1:
            return containers[0]
        else:
            raise RuntimeError(f"more than one container for job {job_uuid}, {containers}")
        pass

    def is_any_container_running(self, job_uuid: str) -> bool:
        containers = self.autodl_client.container_list(job_uuid)
        if containers is None or len(containers) == 0:
            return False
        return any(c.status == "running" for c in containers)

    def parse_ssh_command(self, ssh_command: str) -> Tuple[str, str, int]:
        # ssh -p port root@ip
        parts = ssh_command.split()
        if len(parts) != 4:
            raise ValueError(f"Invalid SSH command format: {ssh_command}")
        port = parts[2]
        user_host = parts[3]
        user, host = user_host.split('@')
        return user, host, port


    def download_job_output_from_container(self, job_uuid: str, job_desc: JobDescription, local_path: str, ignores=""):
        # download output path to local path
        container = self.get_job_conainter(job_uuid)
        if container is None:
            logger.info(f"can't find container for job {job_uuid}, maybe job is finished")
            return 
        output_path = job_desc.working_dir + "/" + job_desc.output_dir + "/"

        ssh_command = container.info.ssh_command
        password = container.info.root_password
        ssh_user, ssh_host, ssh_port = self.parse_ssh_command(ssh_command)
        logger.info(f"download output from {ssh_user}@{ssh_host}:{output_path} to {local_path}")
        ssh_utils.download_file(output_path, local_path, host=ssh_host, username=ssh_user, password=password, port=int(ssh_port), ignores=ignores)
        logger.info(f"download output finished")
        pass

    def download_job_output_from_cos(self, job_uuid: str, local_path: str):
        # download all files in job dir to local path
        url = self.get_job_output_url(job_uuid)
        if url == "":
            logger.info(f"can't find output url for job {job_uuid}, maybe job is not finished")
            return
        storage.download_file(url, local_path)
        pass
    
    @classmethod
    def default_job_description(cls) -> JobDescription:
        job_desc = JobDescription()
        job_desc.command = "python3"
        job_desc.args = ["-c", "\"print('Hello World')\""]
        job_desc.working_dir = "/root/autodl-tmp/"
        job_desc.output_dir = "output"
        job_desc.env = dict()
        job_desc.priority = 0
        job_desc.description = ""
        job_desc.input_paths = []
        job_desc.gpu_num = 1
        job_desc.image = "ml_backend:0.0.1"
        return job_desc
    
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
    
    @classmethod
    def default_input_path(cls, train_id: str) -> str:
        return f"cos://ml_backend/autodl/input/{train_id}/"