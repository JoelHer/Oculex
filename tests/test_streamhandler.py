import unittest
from unittest.mock import patch, MagicMock
import time

from backend.StreamHandler import StreamHandler


class TestDeltaTracking(unittest.TestCase):
    def setUp(self):
        # Create a fake StreamHandler with a mocked getOcrResult
        self.logger = MagicMock()
        self.handler = StreamHandler(self.logger,"test", "rtsp://example.com/stream", {}, {}, {}, None)
        self.handler.getOcrResult = MagicMock()

    @patch("time.time", return_value=200.0)
    def test_accepts_first_value(self, mock_time):
        """Should accept if there's no last value/timestamp"""
        self.handler.getOcrResult.return_value = {"aggregate": {"value": None, "timestamp": None}}
        self.assertTrue(self.handler.delta_tracking(new_value=100, increase=10, timespan_seconds=60))

    @patch("time.time", return_value=200.0)
    def test_same_value_is_accepted(self, mock_time):
        """Should accept if value is unchanged"""
        self.handler.getOcrResult.return_value = {"aggregate": {"value": 100, "timestamp": 150}}
        self.assertTrue(self.handler.delta_tracking(new_value=100, increase=10, timespan_seconds=60))

    @patch("time.time", return_value=200.0)
    def test_within_allowed_change(self, mock_time):
        """Should accept if change <= allowed_change"""
        # elapsed = 50s, rate_per_second = 10/60 ≈ 0.166, allowed ≈ 8.3
        self.handler.getOcrResult.return_value = {"aggregate": {"value": 100, "timestamp": 150}}
        self.assertTrue(self.handler.delta_tracking(new_value=107, increase=10, timespan_seconds=60))

    @patch("time.time", return_value=200.0)
    def test_exceeds_allowed_change(self, mock_time):
        """Should reject if change > allowed_change"""
        # elapsed = 50s, allowed ≈ 8.3, but actual change = 20
        self.handler.getOcrResult.return_value = {"aggregate": {"value": 100, "timestamp": 150}}
        self.assertFalse(self.handler.delta_tracking(new_value=120, increase=10, timespan_seconds=60))

    @patch("time.time", return_value=200.0)
    def test_timespan_zero_raises(self, mock_time):
        """Should raise ValueError if timespan <= 0"""
        self.handler.getOcrResult.return_value = {"aggregate": {"value": 100, "timestamp": 150}}
        with self.assertRaises(ValueError):
            self.handler.delta_tracking(new_value=110, increase=10, timespan_seconds=0)

    @patch("time.time", return_value=100.0)
    def test_negative_elapsed_raises(self, mock_time):
        """Should raise ValueError if elapsed < 0"""
        self.handler.getOcrResult.return_value = {"aggregate": {"value": 100, "timestamp": 250}}
        with self.assertRaises(ValueError):
            self.handler.delta_tracking(new_value=110, increase=10, timespan_seconds=-1)

    @patch("time.time", return_value=200.0)
    def test_negative_allowed_decrease(self, mock_time):
        """Should act the same, even if increase < 0"""
        self.handler.getOcrResult.return_value = {"aggregate": {"value": 100, "timestamp": 150}}
        self.assertTrue(self.handler.delta_tracking(new_value=95, increase=10, timespan_seconds=60))

    @patch("time.time", return_value=200.0)
    def test_negative_increase_exceeds_allowed(self, mock_time):
        """Should reject if decrease > allowed_change"""
        # elapsed = 50s, allowed ≈ 8.3, but actual change = 20
        self.handler.getOcrResult.return_value = {"aggregate": {"value": 100, "timestamp": 150}}
        self.assertFalse(self.handler.delta_tracking(new_value=80, increase=10, timespan_seconds=60))

if __name__ == "__main__":
    unittest.main()
