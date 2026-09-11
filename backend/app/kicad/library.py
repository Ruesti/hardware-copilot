"""Kuratierte Bauteil-Bibliothek: MPN → KiCad-Symbol + Rollen-Pin-Map.

Pin-Fakten kommen ausschließlich aus dieser Bibliothek (bzw. den referenzierten
KiCad-Symbolen), nie vom LLM — siehe Spec 2026-09-06-kicad-export-design.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

LIBRARY_PATH = Path(__file__).resolve().parent.parent.parent / "library" / "parts.yaml"


@dataclass(frozen=True)
class LibraryPart:
    lib_id: str
    footprint: str
    role_to_pin: dict[str, list[str]]
    validated: bool = False
    datasheet: str = ""


@dataclass
class Library:
    parts: dict[str, LibraryPart] = field(default_factory=dict)
    type_fallbacks: dict[str, LibraryPart] = field(default_factory=dict)

    def for_component(self, mpn: str | None, comp_type: str | None) -> LibraryPart | None:
        if mpn and mpn in self.parts:
            return self.parts[mpn]
        if comp_type and comp_type in self.type_fallbacks:
            return self.type_fallbacks[comp_type]
        return None

    def is_fallback(self, mpn: str | None) -> bool:
        return not (mpn and mpn in self.parts)


def _to_part(raw: dict) -> LibraryPart:
    return LibraryPart(
        lib_id=raw["lib_id"],
        footprint=raw.get("footprint", ""),
        role_to_pin={k: [str(p) for p in v] for k, v in (raw.get("role_to_pin") or {}).items()},
        validated=bool(raw.get("validated", False)),
        datasheet=raw.get("datasheet", ""),
    )


def load_library(path: Path = LIBRARY_PATH) -> Library:
    data = yaml.safe_load(path.read_text())
    return Library(
        parts={mpn: _to_part(raw) for mpn, raw in (data.get("parts") or {}).items()},
        type_fallbacks={t: _to_part(raw) for t, raw in (data.get("type_fallbacks") or {}).items()},
    )
