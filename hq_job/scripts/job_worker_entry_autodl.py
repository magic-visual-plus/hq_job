from hq_job.job_engine import JobDescription
from hq_job import storage
import os
import loguru
import subprocess
import sys

logger = loguru.logger

if __name__ == '__main__':
    logger.info("env: " + str(os.environ))
    job_desc = JobDescription.from_env(os.environ)

    logger.info(f"Job Description: {job_desc.__dict__}")
    working_dir = job_desc.working_dir
    output_dir = os.path.join(working_dir, job_desc.output_dir)
    os.makedirs(working_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    #download input files
    for input_path in job_desc.input_paths:
        logger.info(f"Downloading input file: {input_path}")
        storage.download_file(input_path, os.path.join(working_dir, os.path.basename(input_path)))
        pass

    # run the command
    process = subprocess.Popen(
        args=job_desc.command + " " + " ".join(job_desc.args),
        cwd=working_dir,
        env=os.environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        shell=True,
        start_new_session=True
    )
    print('job output begin-----------------------------')
    sys.stdout.flush()
    for line in process.stdout:
        print(line.decode('utf-8').rstrip())
        sys.stdout.flush()
        pass
    print('job output end-------------------------------')
    sys.stdout.flush()
    return_code = process.wait()
    logger.info(f"Job completed with return code {return_code}")
    pass

    container_uuid = os.environ.get("AutoDLContainerUUID", "unknown_container")

    # upload output files
    storage.upload_file(
        output_dir + '/', f"cos://ml_backend/autodl/{container_uuid}/")
    pass