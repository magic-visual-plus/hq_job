

import os
from .base import StorageBase
import fabric


class SCPStorage(StorageBase):
    def __init__(self, host, username, password=None, port=22, key_file=None) -> None:
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.key_file = key_file

    def download_file(self, remote_path: str, local_path: str, ignores: str = ""):
        if remote_path.endswith("/"):
            # recursive download
            connect_kwargs = dict()
            if self.password is not None:
                connect_kwargs["password"] = self.password
                pass
            if self.key_file is not None:
                connect_kwargs["key_filename"] = self.key_file
                pass
            with fabric.Connection(host=self.host, user=self.username, port=self.port, connect_kwargs=connect_kwargs) as conn:
                # pack dir
                basename = os.path.basename(remote_path.rstrip("/"))
                tmp_file = f"/tmp/{basename}.tar.gz"
                pack_command = f"rm -rf {tmp_file} && tar -czf {tmp_file} -C {remote_path}"
                if len(ignores) > 0:
                    pack_command += f" --exclude='{ignores}'"
                    pass
                pack_command += " ."
                conn.run(pack_command)
                try:
                    if os.path.exists(tmp_file):
                        # remove old tmp file
                        os.remove(tmp_file)
                        pass
                    conn.get(remote=tmp_file, local=tmp_file)
                    target_path = os.path.join(local_path, basename)
                    if os.path.exists(target_path):
                        raise RuntimeError(f"target path {target_path} exists")
                    os.makedirs(target_path, exist_ok=True)
                    os.system(f"tar -xzf {tmp_file} -C {target_path}")
                finally:
                    if os.path.exists(tmp_file):
                        os.remove(tmp_file)
                        pass
                    conn.run(f"rm -rf {tmp_file}")
                    pass
                pass
            pass
        else:
            self.download_file_single(remote_path, local_path)
        pass
    
    def download_file_single(self, remote_path: str, local_path: str):
        connect_kwargs = dict()
        if self.password is not None:
            connect_kwargs["password"] = self.password
            pass
        if self.key_file is not None:
            connect_kwargs["key_filename"] = self.key_file
            pass
        
        with fabric.Connection(host=self.host, user=self.username, port=self.port, connect_kwargs=connect_kwargs) as conn:
            conn.get(remote=remote_path, local=local_path)
            pass
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

