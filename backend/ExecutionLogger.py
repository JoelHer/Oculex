import sqlite3
from datetime import datetime

class ExecutionLogger:
    def __init__(self, stream_manager, db_path="/data/logs.db"):
        self.stream_manager = stream_manager
        self.conn = sqlite3.connect(db_path)
        self._setup_db()

    def _setup_db(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id TEXT,
            level TEXT,
            message TEXT,
            timestamp TEXT
        )
        """)
        self.conn.commit()

    def _validate_stream(self, stream_id):
        stream = self.stream_manager.get_stream(stream_id)
        if not stream:
            raise ValueError(f"Stream ID '{stream_id}' does not exist.")

    def _write_log(self, stream_id, level, message):
        print(f"[{level}] [{stream_id}] {message}")
        timestamp = int(datetime.now().timestamp())
        # Persist to DB
        self.conn.execute(
            "INSERT INTO logs (stream_id, level, message, timestamp) VALUES (?, ?, ?, ?)",
            (stream_id, level, message, timestamp)
        )
        self.conn.commit()

    def info(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._write_log(stream_id, "INFO", method_name + message)

    def error(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._write_log(stream_id, "ERROR", method_name + message)

    def warning(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._write_log(stream_id, "WARNING", method_name + message)

    def debug(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._write_log(stream_id, "DEBUG", method_name + message)
