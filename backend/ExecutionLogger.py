import sqlite3
import queue
import threading
from datetime import datetime
import time as time_module
import asyncio

class ExecutionLogger:
    def __init__(self, stream_manager, db_path="/data/logs.db", ws_manager=None):
        self.stream_manager = stream_manager
        self.db_path = db_path
        self.ws_manager = ws_manager

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
                break  

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

            if self.ws_manager:
                self.ws_manager.loop.call_soon_threadsafe(
                    asyncio.create_task,
                    self.ws_manager.broadcast({
                        "type": "logger/log",
                        "stream_id": stream_id,
                        "message": message,
                        "level": level,
                        "timestamp": timestamp,
                    })
                )
            else:
                print(f"[WARN][ExecutionLogger] No WS manager to broadcast log.")

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

    def get_logs(self, stream_id, limit=1000):
        """
        Retrieve logs for a given stream_id sorted by timestamp (newest first).
        limit caps the number of returned rows (default 1000, max 50000).
        Returns a list of dicts: {id, stream_id, level, message, timestamp, iso}
        """
        self._validate_stream(stream_id)

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 1000
        if limit <= 0:
            limit = 1000

        MAX_LIMIT = 50000
        if limit > MAX_LIMIT:
            limit = MAX_LIMIT

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT id, stream_id, level, message, timestamp FROM logs WHERE stream_id = ? ORDER BY timestamp DESC LIMIT ?",
                (stream_id, limit),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        conn2 = sqlite3.connect(self.db_path)
        conn2.row_factory = sqlite3.Row
        try:
            cur = conn2.execute(
                "SELECT count(*) FROM logs WHERE stream_id = ?",
                (stream_id,), # DONT FORGET THE COMMA
            )
            rowsTotal = cur.fetchall()
            print(" [ExecutionLogger] Total logs for stream", stream_id, ":", rowsTotal[0][0])
        finally:
            conn2.close()

        result = []
        for r in rows:
            ts = r["timestamp"]
            iso = None
            try:
                iso = datetime.fromtimestamp(int(ts)).isoformat()
            except Exception:
                iso = None
            result.append({
                "id": r["id"],
                "stream_id": r["stream_id"],
                "level": r["level"],
                "message": r["message"],
                "timestamp": ts,
                "iso": iso,
            })
        return {
            "stream_id": stream_id,
            "logs": result,
            "total": rowsTotal[0][0],
            "limit": limit
        }
