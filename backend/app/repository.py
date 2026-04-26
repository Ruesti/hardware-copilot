from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.db import get_connection
from app.models import (
    BlockConnection,
    ChatMessage,
    ComponentCreate,
    ComponentItem,
    ComponentUpdate,
    ConnectionCreate,
    DatasheetRecord,
    DesignBlock,
    DesignBlockCreate,
    DesignBlockUpdate,
    DiagramBlock,
    Project,
    ProjectCreate,
    ProjectListItem,
    ProjectUpdate,
    Requirement,
    RequirementCreate,
    RequirementUpdate,
    TrustLevel,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _trust(value: str) -> TrustLevel:
    return TrustLevel(value)


# ── Projects ──────────────────────────────────────────────────────────────────

def list_projects() -> list[ProjectListItem]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, phase, created_at FROM projects ORDER BY created_at DESC"
        ).fetchall()
    return [
        ProjectListItem(
            id=r["id"], name=r["name"], phase=r["phase"], created_at=r["created_at"]
        )
        for r in rows
    ]


def get_project(project_id: str) -> Project | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, phase, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
    if row is None:
        return None
    return Project(
        id=row["id"],
        name=row["name"],
        phase=row["phase"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_project(data: ProjectCreate) -> Project:
    now = _now()
    pid = _gen_id("prj")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, phase, created_at, updated_at) VALUES (?,?,?,?,?)",
            (pid, data.name, data.phase, now, now),
        )
    return Project(id=pid, name=data.name, phase=data.phase, created_at=now, updated_at=now)


def update_project(project_id: str, data: ProjectUpdate) -> Project | None:
    project = get_project(project_id)
    if project is None:
        return None
    now = _now()
    name = data.name if data.name is not None else project.name
    phase = data.phase if data.phase is not None else project.phase
    with get_connection() as conn:
        conn.execute(
            "UPDATE projects SET name=?, phase=?, updated_at=? WHERE id=?",
            (name, phase, now, project_id),
        )
    return Project(
        id=project_id, name=name, phase=phase,
        created_at=project.created_at, updated_at=now,
    )


def delete_project(project_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    return cur.rowcount > 0


# ── Requirements ──────────────────────────────────────────────────────────────

def list_requirements(project_id: str) -> list[Requirement]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, description, status FROM requirements "
            "WHERE project_id=? ORDER BY order_index ASC, id ASC",
            (project_id,),
        ).fetchall()
    return [
        Requirement(id=r["id"], title=r["title"], description=r["description"], status=r["status"])
        for r in rows
    ]


def create_requirement(project_id: str, data: RequirementCreate) -> Requirement:
    rid = _gen_id("req")
    with get_connection() as conn:
        idx = (
            conn.execute(
                "SELECT COALESCE(MAX(order_index)+1, 0) AS n FROM requirements WHERE project_id=?",
                (project_id,),
            ).fetchone()["n"]
        )
        conn.execute(
            "INSERT INTO requirements (id, project_id, title, description, status, order_index) "
            "VALUES (?,?,?,?,?,?)",
            (rid, project_id, data.title, data.description, data.status, idx),
        )
    return Requirement(id=rid, title=data.title, description=data.description, status=data.status)


def update_requirement(project_id: str, req_id: str, data: RequirementUpdate) -> Requirement | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, title, description, status FROM requirements WHERE id=? AND project_id=?",
            (req_id, project_id),
        ).fetchone()
        if row is None:
            return None
        title = data.title if data.title is not None else row["title"]
        desc = data.description if data.description is not None else row["description"]
        status = data.status if data.status is not None else row["status"]
        conn.execute(
            "UPDATE requirements SET title=?, description=?, status=? WHERE id=?",
            (title, desc, status, req_id),
        )
    return Requirement(id=req_id, title=title, description=desc, status=status)


def delete_requirement(project_id: str, req_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM requirements WHERE id=? AND project_id=?", (req_id, project_id)
        )
    return cur.rowcount > 0


# ── Blocks ────────────────────────────────────────────────────────────────────

def list_blocks(project_id: str) -> list[DesignBlock]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, description, trust_level FROM blocks "
            "WHERE project_id=? ORDER BY order_index ASC, id ASC",
            (project_id,),
        ).fetchall()
    return [
        DesignBlock(
            id=r["id"], name=r["name"], description=r["description"],
            trust_level=_trust(r["trust_level"]),
        )
        for r in rows
    ]


def create_block(project_id: str, data: DesignBlockCreate) -> DesignBlock:
    bid = _gen_id("blk")
    with get_connection() as conn:
        idx = conn.execute(
            "SELECT COALESCE(MAX(order_index)+1, 0) AS n FROM blocks WHERE project_id=?",
            (project_id,),
        ).fetchone()["n"]
        conn.execute(
            "INSERT INTO blocks (id, project_id, name, description, trust_level, order_index) "
            "VALUES (?,?,?,?,?,?)",
            (bid, project_id, data.name, data.description, data.trust_level.value, idx),
        )
    return DesignBlock(id=bid, name=data.name, description=data.description, trust_level=data.trust_level)


def update_block(project_id: str, blk_id: str, data: DesignBlockUpdate) -> DesignBlock | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, description, trust_level FROM blocks WHERE id=? AND project_id=?",
            (blk_id, project_id),
        ).fetchone()
        if row is None:
            return None
        name = data.name if data.name is not None else row["name"]
        desc = data.description if data.description is not None else row["description"]
        tl = data.trust_level.value if data.trust_level is not None else row["trust_level"]
        conn.execute(
            "UPDATE blocks SET name=?, description=?, trust_level=? WHERE id=?",
            (name, desc, tl, blk_id),
        )
    return DesignBlock(id=blk_id, name=name, description=desc, trust_level=_trust(tl))


def delete_block(project_id: str, blk_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM blocks WHERE id=? AND project_id=?", (blk_id, project_id)
        )
    return cur.rowcount > 0


def bulk_create_blocks(project_id: str, blocks: list[DesignBlockCreate]) -> list[DesignBlock]:
    created = []
    for b in blocks:
        created.append(create_block(project_id, b))
    return created


# ── Components ────────────────────────────────────────────────────────────────

def _row_to_component(row: Any) -> ComponentItem:
    return ComponentItem(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        value=row["value"],
        package=row["package"],
        manufacturer=row["manufacturer"],
        mpn=row["mpn"],
        description=row["description"] or "",
        trust_level=_trust(row["trust_level"]),
        block_id=row["block_id"],
    )


def list_components(project_id: str) -> list[ComponentItem]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, block_id, name, type, value, package, manufacturer, mpn, description, trust_level "
            "FROM components WHERE project_id=? ORDER BY order_index ASC, id ASC",
            (project_id,),
        ).fetchall()
    return [_row_to_component(r) for r in rows]


def create_component(project_id: str, data: ComponentCreate) -> ComponentItem:
    cid = _gen_id("cmp")
    with get_connection() as conn:
        idx = conn.execute(
            "SELECT COALESCE(MAX(order_index)+1, 0) AS n FROM components WHERE project_id=?",
            (project_id,),
        ).fetchone()["n"]
        conn.execute(
            "INSERT INTO components "
            "(id, project_id, block_id, name, type, value, package, manufacturer, mpn, description, trust_level, order_index) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                cid, project_id, data.block_id, data.name, data.type,
                data.value, data.package, data.manufacturer, data.mpn,
                data.description, data.trust_level.value, idx,
            ),
        )
    return ComponentItem(
        id=cid, name=data.name, type=data.type, value=data.value,
        package=data.package, manufacturer=data.manufacturer, mpn=data.mpn,
        description=data.description, trust_level=data.trust_level, block_id=data.block_id,
    )


def update_component(project_id: str, cmp_id: str, data: ComponentUpdate) -> ComponentItem | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, block_id, name, type, value, package, manufacturer, mpn, description, trust_level "
            "FROM components WHERE id=? AND project_id=?",
            (cmp_id, project_id),
        ).fetchone()
        if row is None:
            return None
        name = data.name if data.name is not None else row["name"]
        ctype = data.type if data.type is not None else row["type"]
        value = data.value if data.value is not None else row["value"]
        package = data.package if data.package is not None else row["package"]
        mfr = data.manufacturer if data.manufacturer is not None else row["manufacturer"]
        mpn = data.mpn if data.mpn is not None else row["mpn"]
        desc = data.description if data.description is not None else row["description"]
        tl = data.trust_level.value if data.trust_level is not None else row["trust_level"]
        bid = data.block_id if data.block_id is not None else row["block_id"]
        conn.execute(
            "UPDATE components SET name=?, type=?, value=?, package=?, manufacturer=?, mpn=?, "
            "description=?, trust_level=?, block_id=? WHERE id=?",
            (name, ctype, value, package, mfr, mpn, desc, tl, bid, cmp_id),
        )
    return ComponentItem(
        id=cmp_id, name=name, type=ctype, value=value, package=package,
        manufacturer=mfr, mpn=mpn, description=desc or "",
        trust_level=_trust(tl), block_id=bid,
    )


def delete_component(project_id: str, cmp_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM components WHERE id=? AND project_id=?", (cmp_id, project_id)
        )
    return cur.rowcount > 0


def bulk_create_components(project_id: str, items: list[dict[str, Any]]) -> list[ComponentItem]:
    created = []
    blocks = {b.name: b.id for b in list_blocks(project_id)}
    for item in items:
        block_id = blocks.get(item.get("block_name", ""))
        data = ComponentCreate(
            name=item.get("name", ""),
            type=item.get("type"),
            value=item.get("value"),
            package=item.get("package"),
            manufacturer=item.get("manufacturer"),
            mpn=item.get("mpn"),
            description=item.get("description", ""),
            trust_level=TrustLevel(item.get("trust_level", "parsed")),
            block_id=block_id,
        )
        created.append(create_component(project_id, data))
    return created


# ── Chat ──────────────────────────────────────────────────────────────────────

def list_chat_messages(project_id: str) -> list[ChatMessage]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, role, content FROM chat_messages "
            "WHERE project_id=? ORDER BY order_index ASC, id ASC",
            (project_id,),
        ).fetchall()
    return [ChatMessage(id=r["id"], role=r["role"], content=r["content"]) for r in rows]


def add_chat_message(project_id: str, role: str, content: str) -> ChatMessage:
    mid = _gen_id("msg")
    now = _now()
    with get_connection() as conn:
        idx = conn.execute(
            "SELECT COALESCE(MAX(order_index)+1, 0) AS n FROM chat_messages WHERE project_id=?",
            (project_id,),
        ).fetchone()["n"]
        conn.execute(
            "INSERT INTO chat_messages (id, project_id, role, content, order_index, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (mid, project_id, role, content, idx, now),
        )
    return ChatMessage(id=mid, role=role, content=content)


def clear_chat_messages(project_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_messages WHERE project_id=?", (project_id,))


# ── Datasheets ────────────────────────────────────────────────────────────────

def list_datasheets(project_id: str) -> list[DatasheetRecord]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, project_id, component_id, filename, extracted_data, created_at "
            "FROM datasheets WHERE project_id=? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
    return [
        DatasheetRecord(
            id=r["id"],
            project_id=r["project_id"],
            component_id=r["component_id"],
            filename=r["filename"],
            extracted_data=json.loads(r["extracted_data"] or "{}"),
            created_at=r["created_at"],
        )
        for r in rows
    ]


def save_datasheet(
    project_id: str,
    filename: str,
    extracted_data: dict[str, Any],
    component_id: str | None = None,
) -> DatasheetRecord:
    did = _gen_id("ds")
    now = _now()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO datasheets (id, project_id, component_id, filename, extracted_data, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (did, project_id, component_id, filename, json.dumps(extracted_data), now),
        )
    return DatasheetRecord(
        id=did, project_id=project_id, component_id=component_id,
        filename=filename, extracted_data=extracted_data, created_at=now,
    )


# ── Project context for Claude ────────────────────────────────────────────────

def get_project_context(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    if project is None:
        return {}
    reqs = list_requirements(project_id)
    blocks = list_blocks(project_id)
    comps = list_components(project_id)
    return {
        "name": project.name,
        "phase": project.phase,
        "requirements": [
            {"id": r.id, "title": r.title, "description": r.description, "status": r.status}
            for r in reqs
        ],
        "blocks": [
            {"id": b.id, "name": b.name, "description": b.description, "trust_level": b.trust_level.value}
            for b in blocks
        ],
        "components": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "manufacturer": c.manufacturer,
                "mpn": c.mpn,
                "description": c.description,
                "trust_level": c.trust_level.value,
                "block_id": c.block_id,
            }
            for c in comps
        ],
    }


def get_chat_history_for_claude(project_id: str) -> list[dict[str, str]]:
    messages = list_chat_messages(project_id)
    result = [
        {"role": m.role, "content": m.content}
        for m in messages
        if m.role in ("user", "assistant")
    ]
    return result[-20:]


# ── Diagram ───────────────────────────────────────────────────────────────────

def get_diagram(project_id: str) -> tuple[list[DiagramBlock], list[BlockConnection]]:
    with get_connection() as conn:
        block_rows = conn.execute(
            """
            SELECT b.id, b.name, b.description, b.trust_level,
                   COALESCE(b.pos_x, 0) AS pos_x,
                   COALESCE(b.pos_y, 0) AS pos_y,
                   COUNT(c.id) AS component_count
            FROM blocks b
            LEFT JOIN components c ON c.block_id = b.id
            WHERE b.project_id = ?
            GROUP BY b.id
            ORDER BY b.order_index ASC
            """,
            (project_id,),
        ).fetchall()
        conn_rows = conn.execute(
            "SELECT id, source_block_id, target_block_id, label, conn_type "
            "FROM connections WHERE project_id = ?",
            (project_id,),
        ).fetchall()

    blocks = [
        DiagramBlock(
            id=r["id"],
            name=r["name"],
            description=r["description"],
            trust_level=_trust(r["trust_level"]),
            pos_x=float(r["pos_x"]),
            pos_y=float(r["pos_y"]),
            component_count=int(r["component_count"]),
        )
        for r in block_rows
    ]
    connections = [
        BlockConnection(
            id=r["id"],
            source_block_id=r["source_block_id"],
            target_block_id=r["target_block_id"],
            label=r["label"],
            conn_type=r["conn_type"],
        )
        for r in conn_rows
    ]
    return blocks, connections


def update_block_position(project_id: str, block_id: str, x: float, y: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE blocks SET pos_x=?, pos_y=? WHERE id=? AND project_id=?",
            (x, y, block_id, project_id),
        )


def create_connection(project_id: str, data: ConnectionCreate) -> BlockConnection:
    cid = _gen_id("con")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO connections "
            "(id, project_id, source_block_id, target_block_id, label, conn_type) "
            "VALUES (?,?,?,?,?,?)",
            (cid, project_id, data.source_block_id, data.target_block_id,
             data.label, data.conn_type),
        )
    return BlockConnection(
        id=cid,
        source_block_id=data.source_block_id,
        target_block_id=data.target_block_id,
        label=data.label,
        conn_type=data.conn_type,
    )


def delete_connection(project_id: str, conn_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM connections WHERE id=? AND project_id=?",
            (conn_id, project_id),
        )
    return cur.rowcount > 0
