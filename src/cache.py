import sqlite3
from datetime import datetime

DB_PATH = "local_cache.db"


class ModelCache:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates the models table if it does not exist."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    hf_repo_id  TEXT NOT NULL,
                    is_deployed INTEGER DEFAULT 0,
                    deployed_at TEXT,
                    last_synced TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_model(self, name: str, source_type: str, hf_repo_id: str):
        """Adds a new model reference to the local registry."""
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO models (name, source_type, hf_repo_id, is_deployed, last_synced)"
                " VALUES (?, ?, ?, 0, ?)",
                (name, source_type, hf_repo_id, now),
            )
            conn.commit()

    def get_all_models(self) -> list[dict]:
        """Returns all registered models and their deployment status."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM models ORDER BY id").fetchall()
            return [dict(row) for row in rows]

    def mark_as_deployed(self, hf_repo_id: str):
        """Sets is_deployed = True and records deployed_at timestamp for the given model."""
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE models SET is_deployed = 1, deployed_at = ? WHERE hf_repo_id = ?",
                (now, hf_repo_id),
            )
            conn.commit()

    def sync_with_hf(self, user_repos: list[str]):
        """
        Compares local cache with actual HF repos and removes orphaned entries.
        PUBLIC_HF_REPO entries are never removed (not owned by the user).
        Updates last_synced for all surviving entries.
        """
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            rows = conn.execute("SELECT id, hf_repo_id, source_type FROM models").fetchall()
            for row in rows:
                if row["source_type"] != "PUBLIC_HF_REPO" and row["hf_repo_id"] not in user_repos:
                    conn.execute("DELETE FROM models WHERE id = ?", (row["id"],))
                else:
                    conn.execute(
                        "UPDATE models SET last_synced = ? WHERE id = ?",
                        (now, row["id"]),
                    )
            conn.commit()
