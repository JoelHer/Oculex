CREATE TABLE IF NOT EXISTS execlogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT,
    level TEXT,
    message TEXT,
    timestamp INTEGER
);