
from .storage.scp import SCPStorage
import fabric


def download_file(remote_path: str, local_path: str, host: str, username: str, password=None, port=22, key_file=None, ignores=""):
    storage = SCPStorage(host=host, username=username, password=password, port=port, key_file=key_file)
    storage.download_file(remote_path, local_path, ignores=ignores)
    pass


def execute_command(command: str, host: str, username: str, password=None, port=22, key_file=None):
    connect_kwargs = dict()
    if password is not None:
        connect_kwargs["password"] = password
        pass
    if key_file is not None:
        connect_kwargs["key_filename"] = key_file
        pass
    
    with fabric.Connection(host=host, user=username, port=port, connect_kwargs=connect_kwargs) as conn:
        result = conn.run(command, hide=True)
        return result.stdout.strip()
    pass