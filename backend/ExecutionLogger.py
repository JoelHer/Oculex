import sqlite3
import queue
import threading
from datetime import datetime
import time as time_module


class ExecutionLogger:
    def __init__(self, stream_manager, db_path="/data/logs.db"):
        self.stream_manager = stream_manager
        self.db_path = db_path

        self.queue = queue.Queue()

        # Start dedicated sqlite thread
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        """Dedicated DB thread. Owns the sqlite connection."""
        conn = sqlite3.connect(self.db_path)
        self._setup_db(conn)

        while True:
            job = self.queue.get()  # blocks

            if job is None:
                break  # optional shutdown support

            stream_id, level, message = job
            timestamp = int(datetime.now().timestamp())

            try:
                conn.execute(
                    "INSERT INTO logs (stream_id, level, message, timestamp) VALUES (?, ?, ?, ?)",
                    (stream_id, level, message, timestamp),
                )
                try:
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"[ERROR][ExecutionLogger] Retention DB error: {e}")

                # retention: remove logs older than 7 days
                cutoff = time_module.time() - 7 * 24 * 60 * 60
                conn.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff,))
                try:
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"[ERROR][ExecutionLogger] Retention DB error: {e}")

                # keep last n entries per stream
                MAX_ENTRIES = 50000 # TODO: make configurable
                conn.execute("""
                    DELETE FROM logs
                    WHERE id IN (
                        SELECT id FROM (
                            SELECT id,
                                   ROW_NUMBER() OVER (PARTITION BY stream_id ORDER BY timestamp DESC) AS rn
                            FROM logs
                        )
                        WHERE rn > ?
                    )
                """, (MAX_ENTRIES,))
                try:
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"[ERROR][ExecutionLogger] Retention DB error: {e}")

            except sqlite3.Error as e:
                print(f"[ERROR][ExecutionLogger] Worker DB error: {e}")

            self.queue.task_done()

    def _setup_db(self, conn):
        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id TEXT,
            level TEXT,
            message TEXT,
            timestamp INTEGER
        )
        """)
        conn.commit()

    # -------------------------
    # Logging front-end methods
    # -------------------------

    def _validate_stream(self, stream_id):
        if not self.stream_manager.get_stream(stream_id):
            raise ValueError(f"Stream ID '{stream_id}' does not exist.")

    def _push(self, stream_id, level, message):
        print(f"[{level}] [{stream_id}] {message}")
        self.queue.put((stream_id, level, message))

    def info(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._push(stream_id, "INFO", method_name + message)

    def error(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._push(stream_id, "ERROR", method_name + message)

    def warning(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._push(stream_id, "WARNING", method_name + message)

    def debug(self, stream_id, message, method_name=""):
        self._validate_stream(stream_id)
        if method_name and not method_name.endswith(": "):
            method_name += ": "
        self._push(stream_id, "DEBUG", method_name + message)
