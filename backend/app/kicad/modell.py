"""Export-Modell (E6): Dataclasses aus dem alten netlist.py; der Bauer aus
Projekt-Positionen folgt in Task 2."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SymbolInstance:
    ref: str
    lib_id: str
    value: str
    footprint: str
    block_name: str
    pin_nets: dict[str, str]
    status: str  # "mapped" | "fallback" | "unverified"
    name: str = ""
    component_id: str = ""
    net_role: str | None = None


@dataclass
class ExportModel:
    instances: list[SymbolInstance] = field(default_factory=list)
    unmapped: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
