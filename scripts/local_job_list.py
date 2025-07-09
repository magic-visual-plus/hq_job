import sys
import pandas as pd
from hq_job.job_engine_local import JobEngineLocal


if __name__ == "__main__":
    engine = JobEngineLocal(sys.argv[1])
    jobs = engine.list()
    if not jobs:
        print("no jobs")
    else:
        columns = ['id', 'status', 'start_time', 'end_time', 'exit_code', 'command', 'args']
        available_columns = [col for col in columns if col in jobs[0]]
        df = pd.DataFrame(jobs)[available_columns]
        df.index = df['id']
        df.drop(columns=['id'], inplace=True)
        print(df)