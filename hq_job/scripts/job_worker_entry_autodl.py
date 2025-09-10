from hq_job.job_engine import JobDescription
from hq_job import storage
from hq_job.job_engine_autodl import JobEngineAutodl
import os
import loguru
import subprocess
import sys
import base64

logger = loguru.logger

if __name__ == '__main__':
    logger.info(f"Starting job worker with args: {sys.argv[1]}")
    job_desc = JobDescription.from_json(base64.b64decode(sys.argv[1].encode('utf-8')).decode('utf-8'))

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
    with open('pid', 'w') as f:
        f.write(str(process.pid))
        pass
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

    container_uuid = os.environ.get("AutoDLContainerUUID")
    if container_uuid is not None:
        job_engine_cls = JobEngineAutodl
        output_path = job_engine_cls.default_output_path(container_uuid)
        pass

    # upload output files
    storage.upload_file(
        output_dir.rstrip('/'), output_path)
    pass