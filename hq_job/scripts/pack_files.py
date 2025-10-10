import hq_job.file_utils
import sys
import os


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    basename = os.path.basename(output_path)
    destination = os.path.dirname(output_path)

    pack_files = hq_job.file_utils.pack_files_by_fixed_size(
        source=input_path,
        destination=destination,
        basename=basename,
        postfix="tar",
        size=1024*1024*1024
    )
    print(pack_files)
    pass