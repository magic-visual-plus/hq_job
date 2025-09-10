
import os
import unittest
from hq_job.job_engine import JobDescription
from hq_job.job_engine_autodl import JobEngineAutodl
from hq_job import storage
import time


class TestAutodlClient(unittest.TestCase):

    def test_run(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        
        job_desc = JobDescription(
            command="python",
            args=["-c", "\"print('Hello, AutoDL!')\"", "; cat test.txt ; echo 'Done.' > output/result.txt"],
            input_paths=["cos://tmps/zouxiaochuan/test.txt"],
            output_dir="output"
        )

        engine = JobEngineAutodl(token=token)
        job_uuid = engine.run(job_desc)

        self.assertIsNotNone(job_uuid)
        
        while True:
            status = engine.status(job_uuid)
            if status != "stopped":
                print(f"Job status: {status}, waiting to complete...")
                time.sleep(1)
                continue
            break

        url = engine.get_job_output_url(job_uuid)
        os.makedirs('output', exist_ok=True)
        storage.download_file(url, 'output')
        local_output_dir = os.path.join('output', job_desc.output_dir)
        self.assertTrue(os.path.exists(f'{local_output_dir}/result.txt'))
        with open(f'{local_output_dir}/result.txt', 'r') as f:
            content = f.read().strip()
            self.assertEqual(content, 'Done.')
            pass
        pass
    
        
        