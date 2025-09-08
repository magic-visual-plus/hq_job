
from qcloud_cos import CosConfig, CosS3Client, CosClientError, CosServiceError
import os
import configparser
import pydantic

class COSFileInfo(pydantic.BaseModel):
    Key: str
    Size: int
    StorageClass: str

class COSClient(object):
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = os.path.join(os.path.expanduser("~"), ".cos.conf")
            pass

        self._load_config(config_file)
        pass

    def _load_config(self, config_file: str):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file {config_file} not found")
            pass
        parser = configparser.ConfigParser()
        parser.read(config_file)
        # print all items
        self.secret_id = parser['common']['secret_id']
        self.secret_key = parser['common']['secret_key']
        self.region = parser['common']['region']
        self.bucket = parser['common']['bucket']
        pass

    
    def download_folder(self, cos_prefix: str, local_dir: str):
        files = self.list_files(prefix=cos_prefix)
        os.makedirs(local_dir, exist_ok=True)
        for f in files:
            relative_path = os.path.relpath(f.Key, cos_prefix)
            local_path = os.path.join(local_dir, relative_path)
            local_folder = os.path.dirname(local_path)
            os.makedirs(local_folder, exist_ok=True)
            self.download_file(f.Key, local_path)
            pass
        pass
    
    def download_file(self, cos_path: str, local_path: str):
        config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key)
        client = CosS3Client(config)
        for i in range(0, 10):
            try:
                response = client.download_file(
                    Bucket=self.bucket,
                    Key=cos_path,
                    DestFilePath=local_path)
                break
            except CosClientError or CosServiceError as e:
                pass
            pass
        pass

    def list_files(self, prefix: str = ""):
        config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key)
        client = CosS3Client(config)

        marker = ""
        files = []
        while True:
            response = client.list_objects(
                Bucket=self.bucket,
                Prefix=prefix,
                Marker=marker,
                MaxKeys=1000
            )
            if 'Contents' in response:
                for item in response['Contents']:
                    files.append(COSFileInfo(**item))
                    pass
                pass
            if response['IsTruncated'] == 'true':
                marker = response['NextMarker']
                pass
            else:
                break
            pass

        return files