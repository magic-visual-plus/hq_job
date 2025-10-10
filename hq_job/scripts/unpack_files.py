
import hq_job.file_utils
import sys
import os

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    basename = os.path.basename(input_path)
    source = os.path.dirname(input_path)

    hq_job.file_utils.unpack_files_and_delete(
        source=source,
        destination=output_path,
        basename=basename,
        postfix="tar"
    )
    pass