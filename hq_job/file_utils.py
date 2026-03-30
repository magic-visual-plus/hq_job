import os
import tarfile
import zipfile


def extract_archive(file_path: str, extract_dir: str = None, delete_after: bool = True) -> str:
    """
    解压压缩文件（支持 zip/tar/tar.gz/tgz）
    
    Args:
        file_path: 压缩文件路径
        extract_dir: 解压目标目录，默认为文件名（去掉扩展名）
        delete_after: 解压后是否删除原文件
    
    Returns:
        解压目录路径，如果不是压缩文件则返回 None
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    basename = os.path.basename(file_path)
    parent_dir = os.path.dirname(file_path)
    
    # 确定解压目录名（文件名去掉扩展名）
    if basename.endswith('.tar.gz'):
        dir_name = basename[:-7]
    elif basename.endswith('.tgz'):
        dir_name = basename[:-4]
    elif basename.endswith('.tar'):
        dir_name = basename[:-4]
    elif basename.endswith('.zip'):
        dir_name = basename[:-4]
    else:
        return None  # 不是支持的压缩格式
    
    if extract_dir is None:
        extract_dir = os.path.join(parent_dir, dir_name)
    
    os.makedirs(extract_dir, exist_ok=True)
    
    # 解压文件
    if basename.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zf:
            zf.extractall(extract_dir)
    else:  # tar, tar.gz, tgz
        with tarfile.open(file_path, 'r:*') as tf:
            tf.extractall(extract_dir)
    
    # 删除原压缩文件
    if delete_after:
        os.remove(file_path)
    
    return extract_dir

def pack_files_by_fixed_size(source, destination, basename, postfix="tar", size=1024*1024*1024):

    if postfix == "tar":
        file_mode = "w"
    else:
        raise ValueError(f"Unsupported postfix: {postfix}")
    
    target_names = []
    if os.path.isfile(source):
        target_name = os.path.join(destination, basename + f"_0.{postfix}")
        target_names.append(target_name)
        with tarfile.open(target_name, "w") as tar:
            tar.add(source, arcname=os.path.basename(source))
            pass
        pass
    else:
        current_size = 0
        current_index = 0
        current_tar = None
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                if current_tar is None or current_size + file_size > size:
                    if current_tar is not None:
                        current_tar.close()
                        pass
                    target_name = os.path.join(destination, f"{basename}_{current_index}.{postfix}")
                    target_names.append(target_name)
                    current_tar = tarfile.open(target_name, file_mode)
                    current_size = 0
                    current_index += 1
                    pass
                current_tar.add(file_path, arcname=os.path.relpath(file_path, source))
                current_size += file_size
                pass
            pass
        if current_tar is not None:
            current_tar.close()
        pass

    return target_names

def unpack_files_and_delete(source, destination, basename, postfix="tar"):
    current_index = 0

    while True:
        target_name = os.path.join(source, f"{basename}_{current_index}.{postfix}")
        if not os.path.exists(target_name):
            break
        with tarfile.open(target_name, "r") as tar:
            tar.extractall(path=destination)
            pass
        os.remove(target_name)
        current_index += 1
        pass
    pass