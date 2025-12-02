import sqlite3
import os
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str, migrations_dir: str):
        self.db_path = db_path
        self.migrations_dir = migrations_dir

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        self.run_migrations()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()


    def _init_db(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER NOT NULL
                )
            """)
            conn.execute("""
                INSERT INTO schema_version (version)
                SELECT 0
                WHERE NOT EXISTS (SELECT 1 FROM schema_version)
            """)

    def run_migrations(self):
        files = sorted(os.listdir(self.migrations_dir))
        with self.connect() as conn:
            cur = conn.execute("SELECT version FROM schema_version")
            current_version = cur.fetchone()["version"]

            for file in files:
                version = int(file.split("_")[0])
                if version > current_version:
                    print(f"[DB] Applying migration {file}")

                    with open(os.path.join(self.migrations_dir, file)) as f:
                        sql = f.read()
                        conn.executescript(sql)

                    conn.execute(
                        "UPDATE schema_version SET version = ?",
                        (version,)
                    )
