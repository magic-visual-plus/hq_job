
import os
from .base import StorageBase


class COSCMDStorage(StorageBase):
    def __init__(self, ):
        super().__init__()

    def download_file(self, remote_path: str, local_path: str):
        if remote_path.startswith("cos://"):
            remote_path = remote_path[len("cos://"):]
            pass
        recursive = ""
        if remote_path.endswith("/"):
            recursive = "-r"
            pass
        os.system(f"coscmd download {recursive} {remote_path} {local_path}")
        pass
    
    def upload_file(self, local_path: str, remote_path: str):
        if remote_path.startswith("cos://"):
            remote_path = remote_path[len("cos://"):]
            pass
        recursive = ""
        if os.path.isdir(local_path):
            recursive = "-r"
            pass
        os.system(f"coscmd upload {recursive} {local_path} {remote_path}")
        pass
    pass

