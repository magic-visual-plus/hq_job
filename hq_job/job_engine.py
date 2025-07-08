
class JobDescription(object):
    
    pass


class JobEngine(object):

    def __init__(self,):
        pass

    def run(self, job: JobDescription) -> int:
        pass

    def execute(self, job_id: int, command: str):
        pass

    def stop(self, job_id: int):
        pass

    def status(self, job_id: int):
        pass

    def list(self,):
        pass

    def remove(self, job_id: int):
        pass
    
    def log(self, job_id: int):
        pass