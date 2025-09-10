

import unittest
from hq_job.storage.cos import COSClient
import os

class TestCosClient(unittest.TestCase):
    def test_list_files(self):
        client = COSClient()
        files = client.list_files(prefix="tmps/zouxiaochuan/test")
        self.assertIsInstance(files, list)
        for f in files:
            print(f)
            pass
        pass

    def test_download_file(self):
        client = COSClient()
        cos_path = "tmps/zouxiaochuan/test"
        local_path = "test_123"
        client.download_file(cos_path, local_path)
        self.assertTrue(os.path.exists(local_path))
        os.remove(local_path)
    pass


if __name__ == "__main__":
    unittest.main()