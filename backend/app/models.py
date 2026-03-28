from __future__ import annotations

from enum import Enum
from typing import Literal

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


class Requirement(ApiModel):
    id: str
    title: str
    description: str
    status: str = "open"


class DesignBlock(ApiModel):
    id: str
    name: str
    description: str
    trust_level: TrustLevel = TrustLevel.NEW


class ComponentItem(ApiModel):
    id: str
    name: str
    value: str | None = None
    package: str | None = None
    manufacturer: str | None = None
    mpn: str | None = None
    description: str = ""
    trust_level: TrustLevel = TrustLevel.NEW
    block_id: str | None = None


class ValidationIssue(ApiModel):
    id: str
    severity: ValidationSeverity
    title: str
    message: str
    related_kind: Literal["requirement", "block", "component"] | None = None
    related_id: str | None = None


class ChatMessage(ApiModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str


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


class ProjectState(ApiModel):
    name: str
    phase: str

    requirements: list[Requirement] = Field(default_factory=list)
    blocks: list[DesignBlock] = Field(default_factory=list)
    components: list[ComponentItem] = Field(default_factory=list)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    chat_messages: list[ChatMessage] = Field(default_factory=list)