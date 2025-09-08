
from .coscmd import COSCMDStorage

def download_file(remote_path: str, local_path: str):
    if remote_path.startswith("cos://"):
        storage = COSCMDStorage()
        storage.download_file(remote_path, local_path)
        pass
    else:
        raise NotImplementedError(f"Unsupported storage type in path: {remote_path}")
    pass

def upload_file(local_path: str, remote_path: str):
    if remote_path.startswith("cos://"):
        storage = COSCMDStorage()
        storage.upload_file(local_path, remote_path)
        pass
    else:
        raise NotImplementedError(f"Unsupported storage type in path: {remote_path}")
    pass