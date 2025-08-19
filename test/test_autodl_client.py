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
    pass


if __name__ == "__main__":
    unittest.main()

