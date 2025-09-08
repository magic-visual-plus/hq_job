

class StorageBase:
    def __init__(self, ):
        pass

    def download_file(self, remote_path: str, local_path: str):
        raise NotImplementedError(
        )
    
    def upload_file(self, local_path: str, remote_path: str):
        raise NotImplementedError(
        )