from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "hardware_copilot.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phase TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS blocks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                trust_level TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS components (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                block_id TEXT,
                name TEXT NOT NULL,
                type TEXT,
                value TEXT,
                package TEXT,
                manufacturer TEXT,
                mpn TEXT,
                description TEXT NOT NULL,
                trust_level TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (block_id) REFERENCES blocks(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS datasheets (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                component_id TEXT,
                filename TEXT NOT NULL,
                extracted_data TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE SET NULL
            );
            """
        )
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS connections (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                source_block_id TEXT NOT NULL,
                target_block_id TEXT NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                conn_type TEXT NOT NULL DEFAULT 'signal',
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (source_block_id) REFERENCES blocks(id) ON DELETE CASCADE,
                FOREIGN KEY (target_block_id) REFERENCES blocks(id) ON DELETE CASCADE
            );
            """
        )
        # Migrations for existing DBs
        if not _column_exists(conn, "components", "type"):
            conn.execute("ALTER TABLE components ADD COLUMN type TEXT")
        if not _column_exists(conn, "blocks", "pos_x"):
            conn.execute("ALTER TABLE blocks ADD COLUMN pos_x REAL DEFAULT 0")
        if not _column_exists(conn, "blocks", "pos_y"):
            conn.execute("ALTER TABLE blocks ADD COLUMN pos_y REAL DEFAULT 0")
