import sys
from hq_job.job_engine_local import JobEngineLocal


if __name__ == "__main__":
    engine = JobEngineLocal(sys.argv[1])
    stop_result = engine.stop(int(sys.argv[2]))
    print(stop_result)
    for job in engine.list():
        print(job)