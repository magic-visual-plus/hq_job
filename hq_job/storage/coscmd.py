
import os
from .base import StorageBase


class COSCMDStorage(StorageBase):
    def __init__(self, ):
        super().__init__()
        self.retry = 3

    def download_file(self, remote_path: str, local_path: str):
        if remote_path.startswith("cos://"):
            remote_path = remote_path[len("cos://"):]
            pass
        recursive = ""
        if remote_path.endswith("/"):
            recursive = "-r -s"
            pass
        retcd = 255
        for itry in range(self.retry):
            retcd = os.system(f"coscmd download {recursive} {remote_path} {local_path}")
            if retcd == 0:
                break
            pass


        if retcd != 0:
            raise RuntimeError(f"coscmd download {remote_path} {local_path} failed: {retcd}")
        pass
    
    def upload_file(self, local_path: str, remote_path: str):
        if remote_path.startswith("cos://"):
            remote_path = remote_path[len("cos://"):]
            pass
        recursive = ""
        if os.path.isdir(local_path):
            recursive = "-r"
            pass

        for itry in range(self.retry):
            retcd = os.system(f"coscmd upload {recursive} {local_path} {remote_path}")
            if retcd == 0:
                break
            pass

        if retcd != 0:
            raise RuntimeError(f"coscmd upload {local_path} {remote_path} failed: {retcd}")
        pass
    pass

