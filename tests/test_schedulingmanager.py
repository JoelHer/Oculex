import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.SchedulingManager import SchedulingManager


class TestSchedulingManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.print_patcher = patch("builtins.print")
        self.mock_print = self.print_patcher.start()
        self.addCleanup(self.print_patcher.stop)

        # Mock StreamManager and StreamHandler
        self.streamManager = MagicMock()
        self.streamHandler = AsyncMock()
        self.streamManager.get_stream.return_value = self.streamHandler

        # Patch AsyncIOScheduler to avoid starting a real scheduler
        patcher = patch("backend.SchedulingManager.AsyncIOScheduler")
        self.addCleanup(patcher.stop)
        self.mockSchedulerClass = patcher.start()
        self.mockScheduler = self.mockSchedulerClass.return_value

        self.manager = SchedulingManager(self.streamManager)

    def test_start_scheduler(self):
        self.manager.start()
        self.mockScheduler.start.assert_called_once()

    def test_add_job_valid(self):
        cron = "* * * * *"
        uid = "123"

        self.manager.add_job(cron, uid)

        self.mockScheduler.add_job.assert_called_once()
        args, kwargs = self.mockScheduler.add_job.call_args
        self.assertEqual(kwargs["id"], f"ocr-job-{uid}")
        self.assertEqual(kwargs["replace_existing"], True)

    def test_add_job_invalid(self):
        # Invalid cron expression should be caught
        uid = "123"
        invalid_cron = "invalid"

        self.manager.add_job(invalid_cron, uid)
        self.mockScheduler.add_job.assert_not_called()

    def test_remove_job(self):
        uid = "123"
        self.manager.remove_job(uid)
        self.mockScheduler.remove_job.assert_called_once_with(f"ocr-job-{uid}")

    def test_list_jobs(self):
        fake_job = MagicMock()
        fake_job.id = "ocr-job-1"
        fake_job.next_run_time = "2025-01-01 00:00:00"
        fake_job.trigger = "cron"
        self.mockScheduler.get_jobs.return_value = [fake_job]

        jobs = self.manager.list_jobs()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "ocr-job-1")
        self.assertEqual(jobs[0]["next_run_time"], "2025-01-01 00:00:00")
        self.assertEqual(jobs[0]["trigger"], "cron")

    async def test_executeScheduling_calls_run_ocr(self):
        uid = "ocr-job-123"
        await self.manager.executeScheduling(uid)

        self.streamManager.get_stream.assert_called_once_with("123")
        self.streamHandler.run_ocr.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
