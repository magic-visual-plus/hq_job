import os
import time
import json
import logging
import subprocess  
import shutil
import sys
import psutil
from datetime import datetime
from typing import Dict, List, Optional

from hq_job.job_engine import JobEngine, JobDescription


class JobEngineLocal(JobEngine):
    
    def __init__(self, jobs_dir: str = "./jobs"):
        """init local job engine"""
        self.jobs_dir = os.path.abspath(jobs_dir)
        self._jobs: Dict[int, Dict] = {}
        
        log_dir = os.path.join(self.jobs_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "job_engine.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                ConsoleAndFileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        os.makedirs(self.jobs_dir, exist_ok=True)
        
        self._load_jobs()
        self._set_next_job_id()

    def _load_jobs(self):
        """scan jobs_dir, load job status from individual status files"""
        self._jobs = {}
        if not os.path.exists(self.jobs_dir):
            os.makedirs(self.jobs_dir, exist_ok=True)
        for name in os.listdir(self.jobs_dir):
            if name.startswith("job_"):
                try:
                    job_id = int(name.split("_")[1])
                except Exception:
                    continue
                job_dir = os.path.join(self.jobs_dir, name)
                status_file = os.path.join(job_dir, "status.json")
                if os.path.exists(status_file):
                    try:
                        with open(status_file, 'r', encoding='utf-8') as f:
                            job_info = json.load(f)
                            job_info['id'] = job_id
                            # ensure all necessary fields exist
                            job_info.setdefault('args', [])
                            job_info.setdefault('env', {})
                            job_info.setdefault('priority', 0)
                            job_info.setdefault('description', '')
                            self._jobs[job_id] = job_info
                    except Exception as e:
                        self.logger.error(f"load job {job_id} status error: {e}")

    def _set_next_job_id(self):
        """set next_job_id based on existing jobs"""
        if not self._jobs:
            self.next_job_id = 1
        else:
            max_job_id = max(self._jobs.keys())
            self.next_job_id = max_job_id + 1

    def _save_job_status(self, job_id: int):
        """save job status to individual status.json file"""
        job_info = self._jobs.get(job_id)
        if not job_info:
            return
        job_dir = self._get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        status_file = os.path.join(job_dir, "status.json")
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(job_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"save job {job_id} status error: {e}")

    def _update_job_status(self, job_id: int, **kwargs):
        """update job status and immediately save to file"""
        if job_id not in self._jobs:
            return
        for key, value in kwargs.items():
            self._jobs[job_id][key] = value
        self._save_job_status(job_id)

    def _get_job_dir(self, job_id: int) -> str:
        """get job dir"""
        return os.path.join(self.jobs_dir, f"job_{job_id}")

    def _get_log_file(self, job_id: int) -> str:
        """get job log file"""
        return os.path.join(self._get_job_dir(job_id), f"job_{job_id}.log")

    def run(self, job: JobDescription) -> int:
        """run job"""
        job_id = self.next_job_id
        self.next_job_id += 1
        job.job_id = job_id
        job_dir = self._get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        # save job info
        job_info = job.to_dict()
        job_info['status'] = 'pending'
        job_info['start_time'] = datetime.now().isoformat()
        self._jobs[job_id] = job_info
        self._save_job_status(job_id)

        worker_script = os.path.join(os.path.dirname(__file__), 'scripts', 'job_worker_entry.py')
        python_exe = sys.executable 
        self.logger.info(f"python_exe: {python_exe}")
        self.logger.info(f"worker_script: {worker_script}")
        self.logger.info(f"job_dir: {job_dir}")
        self.logger.info(f"job_id: {job_id}")
        if sys.platform == 'win32':
            cmd = f'start /B "" "{python_exe}" "{worker_script}" "{job_dir}" "{job_id}"'
            os.system(cmd)
        else:
            cmd = f'nohup "{python_exe}" "{worker_script}" "{job_dir}" "{job_id}" > /dev/null 2>&1 &'
            os.system(cmd)

        return job_id

    def execute(self, job_id: int, command: str):
        """execute command in job"""
        self._load_jobs()
        if job_id not in self._jobs:
            raise ValueError(f"job {job_id} not found")
        
        job_info = self._jobs[job_id]
        if job_info['status'] != 'running':
            raise ValueError(f"job {job_id} is not running")
        
        # get working dir
        job_dir = self._get_job_dir(job_id)
        working_dir = job_info.get('working_dir', job_dir)
        if not os.path.isabs(working_dir):
            working_dir = os.path.join(job_dir, working_dir)
        
        # set env
        env = os.environ.copy()
        env.update(job_info.get('env', {}))
        if job_info.get('output_dir'):
            output_dir = os.path.join(job_dir, job_info['output_dir'])
            env['JOB_OUTPUT_DIR'] = output_dir
            env['OUTPUT_DIR'] = output_dir
        
        # execute command
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                env=env,
                capture_output=True,
                text=True
            )
            
            self.logger.info(f"\nexecute command: {command}")
            self.logger.info(f"time: {datetime.now().isoformat()}")
            self.logger.info(f"working_dir: {working_dir}")
            self.logger.info(f"exit_code: {process.returncode}")
            if process.stdout:
                self.logger.info(f"stdout:\n{process.stdout}")
            if process.stderr:
                self.logger.info(f"stderr:\n{process.stderr}")
            self.logger.info("-" * 30)
                
        except Exception as e:
            self.logger.error(f"\nexecute command: {command}")
            self.logger.error(f"time: {datetime.now().isoformat()}")
            self.logger.error(f"working_dir: {working_dir}")
            self.logger.error(f"error: {str(e)}")
            self.logger.error("-" * 30)
            raise ValueError(f"execute command error: {e}")

    def stop(self, job_id: int):
        """stop job"""
        self._load_jobs()
        if job_id not in self._jobs:
            raise ValueError(f"job {job_id} not found")
        job_info = self._jobs[job_id]
        if job_info['status'] not in ['running', 'postprocessing']:
            raise ValueError(f"job {job_id} is not running or postprocessing")
        try:
            if job_info.get('pid'):
                pid = job_info['pid']
                try:
                    p = psutil.Process(pid)
                    for child in p.children(recursive=True):
                        child.kill()
                    p.kill()
                    for _ in range(10):
                        if not psutil.pid_exists(pid):
                            break
                        time.sleep(0.3)
                except Exception:
                    pass
                if psutil.pid_exists(pid):
                    raise RuntimeError(f"failed to kill process {pid}")
            time.sleep(1)
            self._update_job_status(job_id, status='stopped', end_time=datetime.now().isoformat())
            log_file = self._get_log_file(job_id)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\njob {job_id} stopped by user\n")
                f.write(f"stop time: {self._jobs[job_id]['end_time']}\n")
            return True
        except Exception as e:
            self.logger.error(f"stop job {job_id} error: {e}")
            return False

    def status(self, job_id: int) -> str:
        """get job status"""
        self._load_jobs()
        if job_id not in self._jobs:
            raise ValueError(f"job {job_id} not found")
        return self._jobs[job_id]['status']

    def list(self) -> List[Dict]:
        """list all jobs"""
        self._load_jobs()
        return [
            {
                'id': job_id,
                'command': info['command'],
                'args': info.get('args', []),
                'description': info.get('description', ''),
                'status': info['status'],
                'priority': info.get('priority', 0),
                'working_dir': info.get('working_dir'),
                'output_dir': info.get('output_dir'),
                'start_time': info.get('start_time'),
                'end_time': info.get('end_time'),
                'exit_code': info.get('exit_code'),
                'pid': info.get('pid'),
                'error_message': info.get('error_message')
            }
            for job_id, info in sorted(self._jobs.items(), key=lambda x: x[0], reverse=True)
        ]

    def remove(self, job_id: int):
        self._load_jobs()
        if job_id not in self._jobs:
            raise ValueError(f"job {job_id} not found")
        # stop job if running
        if self._jobs[job_id]['status'] in ['running', 'postprocessing']:
            raise ValueError(f"job {job_id} is running or postprocessing")
        # remove output dir
        job_info = self._jobs[job_id]
        output_dir = job_info.get('output_dir')
        if output_dir:
            shutil.rmtree(output_dir, ignore_errors=True)
        self.logger.info(f"remove job {job_id} output dir: {output_dir}")

    def log(self, job_id: int) -> str:
        """get job log"""
        self._load_jobs()
        if job_id not in self._jobs:
            return f"job {job_id} not found"
        
        log_file = self._get_log_file(job_id)
        if not os.path.exists(log_file):
            return f"job {job_id} log file not found"
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"read job {job_id} log error: {e}"


class ConsoleAndFileHandler(logging.Handler):
    """log to console and file"""
    
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
    def emit(self, record):
        self.console_handler.emit(record)
        self.file_handler.emit(record)