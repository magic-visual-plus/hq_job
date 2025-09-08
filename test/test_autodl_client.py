import unittest
from hq_job.autodl_client import AutodlClient, AutodlImage, AutodlGpuStock
import os


class TestAutodlClient(unittest.TestCase):
    def test_image_list(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        
        client = AutodlClient(token)
        images = client.image_list()
        self.assertIsInstance(images, list)
        for image in images:
            self.assertTrue(hasattr(image, 'id'))
            self.assertTrue(hasattr(image, 'image_name'))
            self.assertTrue(hasattr(image, 'image_uuid'))
            print(f"Image ID: {image.id}, Name: {image.image_name}, UUID: {image.image_uuid}")
            pass
        pass

    def test_gpu_stock_list(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        
        client = AutodlClient(token)
        gpu_stocks = client.gpu_stock_list()
        self.assertGreater(len(gpu_stocks), 0)
        for gpu_type, stock in gpu_stocks.items():
            self.assertTrue(hasattr(stock, 'idle_gpu_num'))
            self.assertTrue(hasattr(stock, 'total_gpu_num'))
            print(f"GPU Type: {gpu_type}, Idle: {stock.idle_gpu_num}, Total: {stock.total_gpu_num}")
            pass
        pass

    def test_blacklist_list(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        client = AutodlClient(token)
        blacklist = client.blacklist_list()
        self.assertIsInstance(blacklist, list)
        for entry in blacklist:
            self.assertTrue(hasattr(entry, 'created_at'))
            self.assertTrue(hasattr(entry, 'data_center'))
            self.assertTrue(hasattr(entry, 'machine_id'))
            print(f"Blacklist Entry: {entry.created_at}, {entry.data_center}, {entry.machine_id}")
            pass
        pass

    def test_create_job(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        client = AutodlClient(token)
        images = client.image_list()
        if not images:
            self.skipTest("No images available to create a job")
            return
        image = [img for img in images if "ml_backend" in img.image_name.lower()][0]
        job_id = client.create_job_deployment(
            name="test_job",
            image_uuid=image.image_uuid,
            replica_num=1,
            parallelism_num=1,
            gpu_name_set=["RTX 4090"],
            cmd="echo Hello World",
            gpu_num=1,
        )
        self.assertIsInstance(job_id, str)
        print(f"Created Job ID: {job_id}")

        deployments = client.deployment_list()
        self.assertTrue(any(deployment.uuid == job_id for deployment in deployments))
        print(f"Deployment {job_id} found in deployment list.")
        pass

    def test_list_deployments(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        client = AutodlClient(token)
        deployments = client.deployment_list()
        self.assertIsInstance(deployments, list)
        for deployment in deployments:
            self.assertTrue(hasattr(deployment, 'uuid'))
            self.assertTrue(hasattr(deployment, 'name'))
            self.assertTrue(hasattr(deployment, 'status'))
            print(f"Deployment UUID: {deployment.uuid}, Name: {deployment.name}, Status: {deployment.status}")
            pass
        pass

    def test_list_containers(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        client = AutodlClient(token)
        deployments = client.deployment_list()
        if not deployments:
            self.skipTest("No deployments available to list containers")
            return
        deployment = deployments[0]
        containers = client.container_list(deployment_uuid=deployment.uuid)
        self.assertIsInstance(containers, list)
        for container in containers:
            self.assertTrue(hasattr(container, 'uuid'))
            self.assertTrue(hasattr(container, 'status'))
            self.assertTrue(hasattr(container, 'gpu_name'))
            print(f"Container UUID: {container.uuid}, Status: {container.status}, GPU: {container.gpu_name}")
            pass
        pass

    def test_list_container_events(self):
        token = os.environ.get("AUTODL_TOKEN", "")
        if not token:
            self.skipTest("AUTODL_TOKEN not set in environment variables")
            return
        client = AutodlClient(token)
        deployments = client.deployment_list()
        if not deployments:
            self.skipTest("No deployments available to list container events")
            return
        deployment = deployments[0]
        events = client.container_event_list(deployment_uuid=deployment.uuid)
        self.assertIsInstance(events, list)
        for event in events:
            self.assertTrue(hasattr(event, 'deployment_container_uuid'))
            self.assertTrue(hasattr(event, 'status'))
            self.assertTrue(hasattr(event, 'created_at'))
            print(f"Event Container UUID: {event.deployment_container_uuid}, Status: {event.status}, Created At: {event.created_at}")
            pass
        pass
    pass


if __name__ == "__main__":
    unittest.main()

