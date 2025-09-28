from backend.StreamManager import StreamManager
from backend.StreamHandler import StreamHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

class SchedulingManager:

    """
    Manager for scheduling OCR jobs.
    """
    def __init__(self, streamManager: StreamManager):
        self.streamManager = streamManager
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.start()
        print("[SchedulingManager] Scheduler started")

    def add_job(self, cron_expression: str, uid: str):
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            self.scheduler.add_job(
                self.executeScheduling,
                trigger,
                args=[uid],
                id=f"ocr-job-{uid}",
                replace_existing=True
            )
            print(f"[SchedulingManager, add_job]: Added job {uid} with {cron_expression}")
        except Exception as e:
            print(f"[SchedulingManager, add_job]: Invalid cron expression: {cron_expression} → {e}")


    def remove_job(self, uid: str):
        """
        Removes a cron job by the given unique identifier.
        """
        try:
            self.scheduler.remove_job(f"ocr-job-{uid}")
        except Exception as e:
            print(f"[SchedulingManager, remove_job]: Failed to remove job {uid} → {e}")
            return
        print(f"[SchedulingManager, remove_job]: Removed job {uid}")

    def list_jobs(self):
        """
        Returns a list with all current cron jobs
        """
        jobs = self.scheduler.get_jobs()
        out = []
        for job in jobs:
            out.append({
                "id": job.id,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            })
        return out

    async def executeScheduling(self, uid:str):
        stream: StreamHandler = self.streamManager.get_stream(uid.removeprefix("ocr-job-"))
        if stream:
            await stream.run_ocr()
