
import os
import unittest
from hq_job.job_engine import JobDescription
from hq_job.job_engine_autodl import JobEngineAutodl
from hq_job import storage
import time
import tempfile


class TestJobEngineAutodl(unittest.TestCase):

    def test_run(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        
        job_desc = JobDescription(
            command="python",
            args=["-c", "\"print('Hello, AutoDL!')\"", "; cat test.txt ; echo 'Done.' > output/result.txt ; sleep 30"],
            input_paths=["cos://tmps/zouxiaochuan/test.txt"],
            output_dir="output"
        )

        engine = JobEngineAutodl(token=token)
        job_uuid = engine.run(job_desc)

        self.assertIsNotNone(job_uuid)
        
        while True:
            if engine.is_any_container_running(job_uuid):
                break
            print("waiting for container to start...")
            time.sleep(1)
            pass

        with tempfile.TemporaryDirectory() as tmpdir:
            engine.download_job_output_from_container(job_uuid, job_desc, local_path=tmpdir)
            self.assertTrue(os.path.exists(f'{tmpdir}/{job_desc.output_dir}/result.txt'))
            with open(f'{tmpdir}/{job_desc.output_dir}/result.txt', 'r') as f:
                content = f.read().strip()
                self.assertEqual(content, 'Done.')
                pass
            pass

        while True:
            status = engine.status(job_uuid)
            if status != "stopped":
                print(f"Job status: {status}, waiting to complete...")
                time.sleep(1)
                continue
            break

        with tempfile.TemporaryDirectory() as tmpdir:
            engine.download_job_output_from_cos(job_uuid, local_path=tmpdir)
            
            local_output_dir = os.path.join(tmpdir, job_desc.output_dir)
            self.assertTrue(os.path.exists(f'{local_output_dir}/result.txt'))
            with open(f'{local_output_dir}/result.txt', 'r') as f:
                content = f.read().strip()
                self.assertEqual(content, 'Done.')
                pass
            pass
        pass
    

    def test_stop(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        job_desc = JobDescription(
            command="python",
            args=["-c", "\"print('Hello, AutoDL!')\"", "; echo \"Done.\" > output/result.txt ; sleep 300"],
            output_dir="output"
        )

        engine = JobEngineAutodl(token=token)
        job_uuid = engine.run(job_desc)
        self.assertIsNotNone(job_uuid)

        while True:
            if engine.is_any_container_running(job_uuid):
                break
            print("waiting for container to start...")
            time.sleep(1)
            pass

        engine.stop(job_uuid)

        cnt = 0
        while True:
            status = engine.status(job_uuid)
            if status != "stopped":
                print("waiting for container to stop...")
                time.sleep(1)
                cnt += 1
                self.assertLess(cnt, 30)
                continue
            break

        with tempfile.TemporaryDirectory() as tmpdir:
            engine.download_job_output_from_cos(job_uuid, local_path=tmpdir)
            local_output_dir = os.path.join(tmpdir, job_desc.output_dir)
            self.assertTrue(os.path.exists(local_output_dir))
            pass
        pass


        
        