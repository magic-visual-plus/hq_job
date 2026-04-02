from hq_job.job_engine import JobDescription
from hq_job import storage
from hq_job import file_utils
from hq_job.job_engine_autodl import JobEngineAutodl
import os
import loguru
import subprocess
import sys
import base64
import time

logger = loguru.logger

def reinstall_numpy():
    os.system("python3 -m pip uninstall -y numpy && rm -rf /root/miniconda3/lib/python3.12/site-packages/numpy*")

    for i in range(5):
        retcd = os.system("python3 -m pip install \"numpy<2.0.0\"")
        if retcd == 0:
            break
        logger.warning("reinstall numpy failed, try again")
        time.sleep(10)
        pass
    pass

if __name__ == '__main__':
    logger.info(f"Starting job worker with args: {sys.argv[1]}")
    job_desc = JobDescription.from_json(base64.b64decode(sys.argv[1].encode('utf-8')).decode('utf-8'))

    logger.info(f"Job Description: {job_desc.__dict__}")
    working_dir = job_desc.working_dir
    output_dir = os.path.join(working_dir, job_desc.output_dir)
    os.makedirs(working_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    logger.info("reinstalling numpy...")
    reinstall_numpy()

    #download input files
    for input_path in job_desc.input_paths:
        logger.info(f"Downloading input file: {input_path}")
        storage.download_file(input_path, os.path.join(working_dir, os.path.basename(input_path)))

    # unpack input files (解压 zip/tar 文件)
    for input_path in job_desc.input_paths:
        file_path = os.path.join(working_dir, os.path.basename(input_path))
        extract_dir = file_utils.extract_archive(file_path, delete_after=True)
        if extract_dir:
            logger.info(f"Unpacked {file_path} to {extract_dir}")

    # run the command
    # 将 job_desc.env 合并到环境变量中
    merged_env = os.environ.copy()
    if job_desc.env:
        merged_env.update(job_desc.env)
    merged_env['HQJOB_WORK_DIR'] = working_dir
    merged_env['HQJOB_JOB_NAME'] = job_desc.name
    
    logger.info("Running command: {} with env: {}".format(job_desc.command, merged_env))
    process = subprocess.Popen(
        args=job_desc.command + " " + " ".join(job_desc.args),
        cwd=working_dir,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        shell=True,
        start_new_session=False
    )
    with open('pid', 'w') as f:
        f.write(str(process.pid))
        pass
    print('job output begin-----------------------------')
    sys.stdout.flush()
    for line in process.stdout:
        print(line.decode('utf-8', errors='ignore').rstrip())
        sys.stdout.flush()
        pass
    print('job output end-------------------------------')
    sys.stdout.flush()
    return_code = process.wait()
    logger.info(f"Job completed with return code {return_code}")
    pass

    container_uuid = os.environ.get("AutoDLDeploymentUUID")
    if container_uuid is not None:
        job_engine_cls = JobEngineAutodl
        output_path = job_engine_cls.default_output_path(container_uuid)
        pass

    # upload output files
    storage.upload_file(
        output_dir.rstrip('/'), output_path)
    pass