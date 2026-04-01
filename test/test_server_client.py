import unittest
from unittest.mock import patch, Mock

from hq_job.server_client import HQJobClient, HQJobClientError
from hq_job.server_models import JobInfo

class TestHQJobClient(unittest.TestCase):

    def setUp(self):
        self.client = HQJobClient(base_url="http://10.8.0.54:9090", token="foresee_hq_job")
        
    def test_list_jobs(self):
        jobs = self.client.list_jobs()
        # import ipdb; ipdb.set_trace()
        print(f'len jobs {len(jobs)}')
        print(jobs)

    @patch('hq_job.server_client.requests.request')
    def test_list_jobs_success(self, mock_request):
        """测试 list_jobs 成功返回任务列表"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "ok",
            "data": [
                {
                    "uuid": "job-uuid-001",
                    "name": "test-job-1",
                    "status": "running",
                    "deployment_type": "Job",
                    "region_sign": "chongqingDC1",
                    "dc_list": ["chongqingDC1"],
                    "gpu_name_set": ["RTX 4090"],
                    "created_at": "2026-03-18T10:00:00+08:00"
                },
                {
                    "uuid": "job-uuid-002",
                    "name": "test-job-2",
                    "status": "stopped",
                    "deployment_type": "Job",
                    "region_sign": "westDC2",
                    "dc_list": ["westDC2"],
                    "gpu_name_set": ["RTX 3090"],
                    "created_at": "2026-03-18T11:00:00+08:00"
                }
            ]
        }
        mock_request.return_value = mock_response

        jobs = self.client.list_jobs()

        self.assertEqual(len(jobs), 2)
        self.assertIsInstance(jobs[0], JobInfo)
        self.assertEqual(jobs[0].uuid, "job-uuid-001")
        self.assertEqual(jobs[0].name, "test-job-1")
        self.assertEqual(jobs[0].status, "running")
        self.assertEqual(jobs[1].uuid, "job-uuid-002")
        self.assertEqual(jobs[1].name, "test-job-2")

        # 验证请求参数
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], "GET")
        self.assertIn("/api/v1/jobs", call_args[0][1])

    @patch('hq_job.server_client.requests.request')
    def test_list_jobs_with_name_filter(self, mock_request):
        """测试 list_jobs 带 name 过滤参数"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "ok",
            "data": [
                {
                    "uuid": "job-uuid-001",
                    "name": "my-task",
                    "status": "running",
                    "deployment_type": "Job",
                    "region_sign": "chongqingDC1",
                    "dc_list": ["chongqingDC1"],
                    "gpu_name_set": ["RTX 4090"],
                    "created_at": "2026-03-18T10:00:00+08:00"
                }
            ]
        }
        mock_request.return_value = mock_response

        jobs = self.client.list_jobs(name="my-task")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].name, "my-task")

        # 验证 name 参数被传递
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]["params"], {"name": "my-task"})

    @patch('hq_job.server_client.requests.request')
    def test_list_jobs_empty(self, mock_request):
        """测试 list_jobs 返回空列表"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "ok",
            "data": []
        }
        mock_request.return_value = mock_response

        jobs = self.client.list_jobs()

        self.assertEqual(len(jobs), 0)

    @patch('hq_job.server_client.requests.request')
    def test_list_jobs_http_error(self, mock_request):
        """测试 list_jobs HTTP 错误"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_request.return_value = mock_response

        with self.assertRaises(HQJobClientError) as ctx:
            self.client.list_jobs()

        self.assertEqual(ctx.exception.code, 401)
        self.assertIn("Invalid token", ctx.exception.message)

    @patch('hq_job.server_client.requests.request')
    def test_list_jobs_business_error(self, mock_request):
        """测试 list_jobs 业务错误"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 502,
            "message": "AutoDL error: network timeout",
            "data": None
        }
        mock_request.return_value = mock_response

        with self.assertRaises(HQJobClientError) as ctx:
            self.client.list_jobs()

        self.assertEqual(ctx.exception.code, 502)
        self.assertIn("AutoDL error", ctx.exception.message)


if __name__ == '__main__':
    unittest.main()
