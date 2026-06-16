def update_job_step(self, job_id: str, step, progress: int):
    job = self.jobs[job_id]
    job["step"] = step
    job["progress"] = progress


def update_job_status(self, job_id: str, status, step=None):
    job = self.jobs[job_id]
    job["status"] = status
    job["step"] = step