CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT,
    level TEXT,
    message TEXT,
    timestamp INTEGER
);

CREATE INDEX IF NOT EXISTS idx_logs_stream
ON logs(stream_id, timestamp DESC);
