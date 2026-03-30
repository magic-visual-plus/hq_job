from hq_job.job_engine import JobDescription
import base64


def get_gen_py_env():
    custom_env = {
                "MY_CUSTOM_VAR": "hello_from_job_desc",
                "METRIC_UUID": "test_value_123"
            }
            
    job_desc = JobDescription(
        command="python",
        args=["/root/foresee/hq_job/test/test_env.py"],
        input_paths=[],
        output_dir="output",
        env=custom_env
    )

    job_str = job_desc.to_json()
    # encode to base64 string
    job_base64 = base64.b64encode(job_str.encode()).decode()
    print(job_base64)
    
    
def test_gen_sh_env():
    custom_env = {
                "MY_CUSTOM_VAR": "hello_from_job_desc",
                "METRIC_UUID": "test_value_123"
            }
            
    job_desc = JobDescription(
        command="bash",
        args=["/root/foresee/hq_job/test/read_env.sh"],
        input_paths=[],
        output_dir="output",
        env=custom_env
    )

    job_str = job_desc.to_json()
    # encode to base64 string
    job_base64 = base64.b64encode(job_str.encode()).decode()
    print(job_base64)

if __name__ == '__main__':
    test_gen_sh_env()