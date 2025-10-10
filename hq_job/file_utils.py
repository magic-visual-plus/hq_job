import os
import tarfile

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