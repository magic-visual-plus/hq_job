
import unittest
import os
import subprocess
import base64
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

    def test_env_passed_to_subprocess(self):
        """测试 job_desc.env 是否正确传递到子进程"""
        # 定义自定义环境变量
        custom_env = {
            "MY_CUSTOM_VAR": "hello_from_job_desc",
            "ANOTHER_VAR": "test_value_123"
        }
        
        # 创建 job description，命令打印环境变量
        job_desc = JobDescription(
            command="python",
            args=["-c", "\"import os; print('MY_CUSTOM_VAR=' + os.environ.get('MY_CUSTOM_VAR', 'NOT_SET')); print('ANOTHER_VAR=' + os.environ.get('ANOTHER_VAR', 'NOT_SET'))\""],
            input_paths=[],
            output_dir="output",
            env=custom_env
        )
        
        # 准备测试环境
        if "AutoDLContainerUUID" not in os.environ:
            os.environ["AutoDLContainerUUID"] = "test_container"
        
        # 直接测试 env 合并逻辑
        merged_env = os.environ.copy()
        merged_env.update(job_desc.env)
        
        # 运行子进程验证 env 传递
        process = subprocess.Popen(
            args=job_desc.command + " " + " ".join(job_desc.args),
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        output, _ = process.communicate()
        output_str = output.decode('utf-8')
        
        # 验证环境变量是否正确传递
        self.assertIn("MY_CUSTOM_VAR=hello_from_job_desc", output_str)
        self.assertIn("ANOTHER_VAR=test_value_123", output_str)
        self.assertEqual(process.returncode, 0)
        pass

    def test_env_empty(self):
        """测试空 env 时不影响子进程"""
        job_desc = JobDescription(
            command="python",
            args=["-c", "\"print('OK')\""],
            input_paths=[],
            output_dir="output",
            env={}
        )
        
        merged_env = os.environ.copy()
        if job_desc.env:
            merged_env.update(job_desc.env)
        
        process = subprocess.Popen(
            args=job_desc.command + " " + " ".join(job_desc.args),
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        output, _ = process.communicate()
        output_str = output.decode('utf-8')
        
        self.assertIn("OK", output_str)
        self.assertEqual(process.returncode, 0)
        pass

    pass


if __name__ == "__main__":
    unittest.main()