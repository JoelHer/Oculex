import sqlite3
import queue
import threading
from datetime import datetime
import time as time_module
import asyncio

class ExecutionLogger:
    def __init__(self, stream_manager, db, ws_manager=None):
        self.stream_manager = stream_manager
        self.db = db
        self.ws_manager = ws_manager

        self.queue = queue.Queue()

        # Start dedicated sqlite thread
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        with self.db.connect() as conn:
            while True:
                job = self.queue.get()
                if job is None:
                    break

                stream_id, level, message = job
                timestamp = int(datetime.now().timestamp())

                try:
                    conn.execute(
                        "INSERT INTO logs (stream_id, level, message, timestamp) VALUES (?, ?, ?, ?)",
                        (stream_id, level, message, timestamp),
                    )

                    # retention: 7 days
                    cutoff = int(time_module.time() - 7 * 24 * 60 * 60)
                    conn.execute(
                        "DELETE FROM logs WHERE timestamp < ?",
                        (cutoff,)
                    )

                    # keep last N per stream
                    MAX_ENTRIES = 50000
                    conn.execute("""
                        DELETE FROM logs
                        WHERE id IN (
                            SELECT id FROM (
                                SELECT id,
                                       ROW_NUMBER() OVER (
                                           PARTITION BY stream_id
                                           ORDER BY timestamp DESC
                                       ) AS rn
                                FROM logs
                            )
                            WHERE rn > ?
                        )
                    """, (MAX_ENTRIES,))

                except Exception as e:
                    print(f"[ExecutionLogger] DB error: {e}")

                # WebSocket broadcast
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

                self.queue.task_done()

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
        self._validate_stream(stream_id)

        limit = max(1, min(int(limit), 50000))

        with self.db.connect() as conn:
            cur = conn.execute(
                """SELECT id, stream_id, level, message, timestamp
                   FROM logs
                   WHERE stream_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (stream_id, limit),
            )
            rows = cur.fetchall()

            cur2 = conn.execute(
                "SELECT count(*) FROM logs WHERE stream_id = ?",
                (stream_id,)
            )
            total = cur2.fetchone()[0]

        result = []
        for r in rows:
            ts = r["timestamp"]
            iso = datetime.fromtimestamp(ts).isoformat() if ts else None
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
            "total": total,
            "limit": limit
        }

