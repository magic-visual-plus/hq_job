import io
import os
import sys
import json
import subprocess
import shutil
from datetime import datetime

def update_status(job_dir, **kwargs):
    status_file = os.path.join(job_dir, 'status.json')
    if not os.path.exists(status_file):
        return
    with open(status_file, 'r', encoding='utf-8') as f:
        job_info = json.load(f)
    for k, v in kwargs.items():
        job_info[k] = v
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(job_info, f, ensure_ascii=False, indent=2)

def copy_output_dir(job_dir, job_info, working_dir, log_file):
    """copy output dir to job dir"""
    output_dir = job_info.get('output_dir')
    if not output_dir:
        print("no output_dir specified, skipping post-process")
        return
    # source output dir
    if os.path.isabs(output_dir):
        source_output_dir = output_dir
    else:
        source_output_dir = os.path.join(working_dir, output_dir)
    
    # target output dir
    target_output_dir = os.path.join(job_dir, output_dir)
    
    # if source output dir exists and has files
    if os.path.exists(source_output_dir) and os.path.isdir(source_output_dir):
        os.makedirs(os.path.dirname(target_output_dir), exist_ok=True)
        if os.path.exists(target_output_dir):
            shutil.rmtree(target_output_dir)
        shutil.copytree(source_output_dir, target_output_dir)
        copied_files = []
        for root, dirs, files in os.walk(target_output_dir):
            for file_name in files:
                rel_path = os.path.relpath(os.path.join(root, file_name), target_output_dir)
                copied_files.append(rel_path)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"output directory copied successfully\n")
            f.write(f"source dir: {source_output_dir}\n")
            f.write(f"target dir: {target_output_dir}\n")
            f.write(f"copied files: {len(copied_files)}\n")
            if copied_files:
                f.write("copied files:\n")
                for file_path in copied_files:
                    f.write(f"  - {file_path}\n")
    else:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"output dir not exists: {source_output_dir}\n")

def main():
    if len(sys.argv) < 3:
        print('Usage: python job_worker_entry.py <job_dir> <job_id>')
        sys.exit(1)
    job_dir = sys.argv[1]
    job_id = int(sys.argv[2])
    status_file = os.path.join(job_dir, 'status.json')
    log_file = os.path.join(job_dir, f'job_{job_id}.log')
    if not os.path.exists(status_file):
        print('status.json not found')
        sys.exit(1)
    with open(status_file, 'r', encoding='utf-8') as f:
        job_info = json.load(f)
    update_status(job_dir, status='running')
    command = job_info['command']
    working_dir = job_info.get('working_dir', job_dir)    # working dir, relative to job dir
    if not os.path.isabs(working_dir):
        working_dir = os.path.join(job_dir, working_dir) # relative to job dir
    os.makedirs(working_dir, exist_ok=True) # create working dir
    env = os.environ.copy() # copy env
    env.update(job_info.get('env', {}))     # update env
    command_str = command + " " + " ".join(job_info.get('args', []))    # command with args
    with open(log_file, 'w', encoding='utf-8', buffering=1) as f:  # line buffering
        f.write(f"job {job_id} started\n")
        f.write(f"command: {command_str}\n")
        f.write(f"working_dir: {working_dir}\n")
        f.write(f"output_dir: {job_info.get('output_dir', 'none')}\n")
        f.write(f"start_time: {job_info['start_time']}\n")
        f.write("-" * 50 + "\n")
        
        env_copy = env.copy() if env else os.environ.copy()
        env_copy['PYTHONUNBUFFERED'] = '1'
        env_copy['PYTHONIOENCODING'] = 'utf-8'

        process = subprocess.Popen(
            command_str,
            cwd=working_dir,
            env=env_copy,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            shell=True,
            start_new_session=True
        )
        update_status(job_dir, pid=process.pid)
        stdout_stream = io.TextIOWrapper(process.stdout, encoding='utf-8', errors='replace', line_buffering=True)
        while True:
            line = stdout_stream.readline()
            if line:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            if process.poll() is not None:
                for remaining in stdout_stream:
                    f.write(remaining)
                    f.flush()
                    os.fsync(f.fileno())
                break
        stdout_stream.close()
    return_code = process.wait()
    # postprocess
    update_status(job_dir, status='postprocessing')
    copy_output_dir(job_dir, job_info, working_dir, log_file)
    if return_code == 0:
        update_status(job_dir, status='completed', end_time=datetime.now().isoformat(), exit_code=return_code)
    else:
        update_status(job_dir, status='failed', end_time=datetime.now().isoformat(), exit_code=return_code)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\njob {job_id} completed\n")
        f.write(f"exit code: {return_code}\n")
        f.write(f"end time: {datetime.now().isoformat()}\n")

if __name__ == '__main__':
    main()
