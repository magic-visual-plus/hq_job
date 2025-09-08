
import unittest
import os
from hq_job.job_engine import JobDescription
from hq_job.job_engine_autodl import JobEngineAutodl


class TestJobWorkerEntryAutodl(unittest.TestCase):

    def test_run(self):
        job_desc = JobDescription(
            command="python",
            args=["-c", "\"print('Hello, AutoDL!')\""],
            input_paths=[],
            output_dir="output"
        )
        if "AutoDLContainerUUID" not in os.environ:
            os.environ["AutoDLContainerUUID"] = "test_container"
            pass
        retcd = os.system(JobEngineAutodl.default_command(job_desc))
        self.assertEqual(retcd, 0)
        pass

    pass


if __name__ == "__main__":
    unittest.main()