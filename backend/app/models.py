from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TrustLevel(str, Enum):
    NEW = "new"
    PARSED = "parsed"
    REVIEWED = "reviewed"
    VALIDATED = "validated"
    PROVEN = "proven"
    TRUSTED_TEMPLATE = "trusted_template"


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    REVIEW_REQUIRED = "review_required"


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectListItem(ApiModel):
    id: str
    name: str
    phase: str
    created_at: str


class Project(ApiModel):
    id: str
    name: str
    phase: str
    created_at: str
    updated_at: str


class ProjectCreate(ApiModel):
    name: str
    phase: str = "Draft"


class ProjectUpdate(ApiModel):
    name: str | None = None
    phase: str | None = None


class ProjectsListResponse(ApiModel):
    items: list[ProjectListItem] = Field(default_factory=list)


# ── Requirements ──────────────────────────────────────────────────────────────

class Requirement(ApiModel):
    id: str
    title: str
    description: str
    status: str = "open"


class RequirementCreate(ApiModel):
    title: str
    description: str = ""
    status: str = "open"


class RequirementUpdate(ApiModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class RequirementsResponse(ApiModel):
    items: list[Requirement] = Field(default_factory=list)


# ── Blocks ────────────────────────────────────────────────────────────────────

class DesignBlock(ApiModel):
    id: str
    name: str
    description: str
    trust_level: TrustLevel = TrustLevel.NEW


class DesignBlockCreate(ApiModel):
    name: str
    description: str = ""
    trust_level: TrustLevel = TrustLevel.NEW


class DesignBlockUpdate(ApiModel):
    name: str | None = None
    description: str | None = None
    trust_level: TrustLevel | None = None


class BlocksResponse(ApiModel):
    items: list[DesignBlock] = Field(default_factory=list)


class BlockPositionUpdate(ApiModel):
    pos_x: float
    pos_y: float


class DiagramBlock(ApiModel):
    id: str
    name: str
    description: str
    trust_level: TrustLevel
    pos_x: float = 0.0
    pos_y: float = 0.0
    component_count: int = 0


class BlockConnection(ApiModel):
    id: str
    source_block_id: str
    target_block_id: str
    label: str = ""
    conn_type: str = "signal"


class ConnectionCreate(ApiModel):
    source_block_id: str
    target_block_id: str
    label: str = ""
    conn_type: str = "signal"


class DiagramResponse(ApiModel):
    blocks: list[DiagramBlock] = Field(default_factory=list)
    connections: list[BlockConnection] = Field(default_factory=list)


# ── Components ────────────────────────────────────────────────────────────────

class ComponentItem(ApiModel):
    id: str
    name: str | None = None
    type: str | None = None
    value: str | None = None
    package: str | None = None
    manufacturer: str | None = None
    mpn: str | None = None
    description: str = ""
    trust_level: TrustLevel = TrustLevel.NEW
    block_id: str | None = None


class ComponentCreate(ApiModel):
    name: str
    type: str | None = None
    value: str | None = None
    package: str | None = None
    manufacturer: str | None = None
    mpn: str | None = None
    description: str = ""
    trust_level: TrustLevel = TrustLevel.NEW
    block_id: str | None = None


class ComponentUpdate(ApiModel):
    name: str | None = None
    type: str | None = None
    value: str | None = None
    package: str | None = None
    manufacturer: str | None = None
    mpn: str | None = None
    description: str | None = None
    trust_level: TrustLevel | None = None
    block_id: str | None = None


class ComponentsResponse(ApiModel):
    items: list[ComponentItem] = Field(default_factory=list)


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(ApiModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str


class ChatMessageCreate(ApiModel):
    content: str


class ChatHistoryResponse(ApiModel):
    items: list[ChatMessage] = Field(default_factory=list)


# ── Validation ────────────────────────────────────────────────────────────────

class ValidationIssue(ApiModel):
    id: str
    severity: ValidationSeverity
    title: str
    message: str
    related_kind: Literal["requirement", "block", "component"] | None = None
    related_id: str | None = None


class ValidationResponse(ApiModel):
    items: list[ValidationIssue] = Field(default_factory=list)


# ── Datasheets ────────────────────────────────────────────────────────────────

class DatasheetRecord(ApiModel):
    id: str
    project_id: str
    component_id: str | None = None
    filename: str
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class DatasheetsResponse(ApiModel):
    items: list[DatasheetRecord] = Field(default_factory=list)


# ── Legacy single-project ─────────────────────────────────────────────────────

class ProjectState(ApiModel):
    name: str
    phase: str
    chat_messages: list[ChatMessage] = Field(default_factory=list)


# ── Selection (frontend-only, kept for compatibility) ─────────────────────────

class RequirementSelection(ApiModel):
    kind: Literal["requirement"]
    id: str


class BlockSelection(ApiModel):
    kind: Literal["block"]
    id: str


class ComponentSelection(ApiModel):
    kind: Literal["component"]
    id: str


Selection = RequirementSelection | BlockSelection | ComponentSelection | None
