
import unittest

from hq_job.job_engine import JobDescription


class TestJobEngine(unittest.TestCase):

    def test_job_description(self):
        job_desc = JobDescription(
            command="python",
            args=["-c", "print('Hello, World!')"],
            working_dir="/tmp",
            output_dir="output",
            env={"EXAMPLE_ENV": "value"},
            priority=5,
            description="A test job"
        )
        
        env_vars = job_desc.to_env()
        self.assertEqual(env_vars["HQJOB_COMMAND"], "python")
        self.assertEqual(env_vars["HQJOB_ARGS"], '["-c", "print(\'Hello, World!\')"]')
        self.assertEqual(env_vars["HQJOB_ENV"], '{"EXAMPLE_ENV": "value"}')
        self.assertEqual(env_vars["HQJOB_PRIORITY"], "5")

        job_desc_restored = JobDescription.from_env(env_vars)
        self.assertEqual(job_desc_restored.command, job_desc.command)
        self.assertEqual(job_desc_restored.args, job_desc.args)
        self.assertEqual(job_desc_restored.working_dir, job_desc.working_dir)
        self.assertEqual(job_desc_restored.output_dir, job_desc.output_dir)
        self.assertEqual(job_desc_restored.env, job_desc.env)
        pass
    pass


if __name__ == '__main__':
    unittest.main()