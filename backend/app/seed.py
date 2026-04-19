from __future__ import annotations

from datetime import datetime, timezone

from app.db import get_connection

DEFAULT_PROJECT_ID = "project-1"


def seed_if_empty() -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM projects").fetchone()
        project_count = int(row["count"])

        if project_count > 0:
            return

        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            INSERT INTO projects (id, name, phase, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                DEFAULT_PROJECT_ID,
                "24V Presence Sensor",
                "Phase 4.1 — SQLite Backend Foundation",
                now,
                now,
            ),
        )

        conn.execute(
            """
            INSERT INTO chat_messages (id, project_id, role, content, order_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "msg-1",
                DEFAULT_PROJECT_ID,
                "assistant",
                "Initial project draft created from sample backend data.",
                0,
                now,
            ),
        )

        conn.executemany(
            """
            INSERT INTO requirements (id, project_id, title, description, status, order_index)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "req-1",
                    DEFAULT_PROJECT_ID,
                    "24V supply input",
                    "The system shall accept a 24V DC input.",
                    "open",
                    0,
                ),
                (
                    "req-2",
                    DEFAULT_PROJECT_ID,
                    "Presence detection",
                    "The system shall detect human presence.",
                    "open",
                    1,
                ),
            ],
        )

        conn.executemany(
            """
            INSERT INTO blocks (id, project_id, name, description, trust_level, order_index)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "blk-1",
                    DEFAULT_PROJECT_ID,
                    "24V Input Protection",
                    "Input polarity and surge protection stage.",
                    "reviewed",
                    0,
                ),
                (
                    "blk-2",
                    DEFAULT_PROJECT_ID,
                    "Buck 24V to 5V",
                    "Primary step-down conversion.",
                    "parsed",
                    1,
                ),
                (
                    "blk-3",
                    DEFAULT_PROJECT_ID,
                    "ESP32-C3 Core",
                    "Main control and connectivity block.",
                    "new",
                    2,
                ),
            ],
        )

        conn.executemany(
            """
            INSERT INTO components (
                id,
                project_id,
                block_id,
                name,
                value,
                package,
                manufacturer,
                mpn,
                description,
                trust_level,
                order_index
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "cmp-1",
                    DEFAULT_PROJECT_ID,
                    "blk-1",
                    "TVS Diode",
                    "SMBJ33A",
                    "SMB",
                    "Littelfuse",
                    "SMBJ33A",
                    "Input surge protection diode.",
                    "reviewed",
                    0,
                ),
                (
                    "cmp-2",
                    DEFAULT_PROJECT_ID,
                    "blk-2",
                    "Buck Regulator",
                    "MP1584EN",
                    "SOIC-8",
                    "MPS",
                    "MP1584EN",
                    "24V to 5V buck regulator.",
                    "parsed",
                    1,
                ),
                (
                    "cmp-3",
                    DEFAULT_PROJECT_ID,
                    "blk-3",
                    "MCU",
                    "ESP32-C3",
                    "QFN32",
                    "Espressif",
                    "ESP32-C3",
                    "Wi-Fi/BLE microcontroller.",
                    "validated",
                    2,
                ),
            ],
        )