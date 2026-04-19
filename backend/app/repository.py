from __future__ import annotations

from app.db import get_connection
from app.models import (
    BlocksResponse,
    ChatMessage,
    ComponentItem,
    ComponentsResponse,
    DesignBlock,
    ProjectState,
    Requirement,
    RequirementsResponse,
    TrustLevel,
)
from app.seed import DEFAULT_PROJECT_ID


def _to_trust_level(value: str) -> TrustLevel:
    return TrustLevel(value)


def get_project_state() -> ProjectState:
    with get_connection() as conn:
        project_row = conn.execute(
            """
            SELECT name, phase
            FROM projects
            WHERE id = ?
            """,
            (DEFAULT_PROJECT_ID,),
        ).fetchone()

        if project_row is None:
            raise RuntimeError("Default project not found in database.")

        chat_rows = conn.execute(
            """
            SELECT id, role, content
            FROM chat_messages
            WHERE project_id = ?
            ORDER BY order_index ASC, id ASC
            """,
            (DEFAULT_PROJECT_ID,),
        ).fetchall()

    return ProjectState(
        name=project_row["name"],
        phase=project_row["phase"],
        chat_messages=[
            ChatMessage(
                id=row["id"],
                role=row["role"],
                content=row["content"],
            )
            for row in chat_rows
        ],
    )


def get_requirements_response() -> RequirementsResponse:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, description, status
            FROM requirements
            WHERE project_id = ?
            ORDER BY order_index ASC, id ASC
            """,
            (DEFAULT_PROJECT_ID,),
        ).fetchall()

    return RequirementsResponse(
        items=[
            Requirement(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
            )
            for row in rows
        ]
    )


def get_blocks_response() -> BlocksResponse:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, trust_level
            FROM blocks
            WHERE project_id = ?
            ORDER BY order_index ASC, id ASC
            """,
            (DEFAULT_PROJECT_ID,),
        ).fetchall()

    return BlocksResponse(
        items=[
            DesignBlock(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                trust_level=_to_trust_level(row["trust_level"]),
            )
            for row in rows
        ]
    )


def get_components_response() -> ComponentsResponse:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                block_id,
                name,
                value,
                package,
                manufacturer,
                mpn,
                description,
                trust_level
            FROM components
            WHERE project_id = ?
            ORDER BY order_index ASC, id ASC
            """,
            (DEFAULT_PROJECT_ID,),
        ).fetchall()

    return ComponentsResponse(
        items=[
            ComponentItem(
                id=row["id"],
                name=row["name"],
                value=row["value"],
                package=row["package"],
                manufacturer=row["manufacturer"],
                mpn=row["mpn"],
                description=row["description"],
                trust_level=_to_trust_level(row["trust_level"]),
                block_id=row["block_id"],
            )
            for row in rows
        ]
    )