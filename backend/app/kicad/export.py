"""Orchestrator: Projekt aus der DB laden → Export-Modell → .kicad_sch + Report."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.repository import get_diagram, list_components

from .library import load_library
from .netlist import build_export_model
from .sch_writer import write_schematic

DEFAULT_SYMBOLS_DIR = Path("/usr/share/kicad/symbols")


@dataclass
class ExportResult:
    schematic_text: str
    report: dict


def run_export(project_id: str, symbols_dir: Path = DEFAULT_SYMBOLS_DIR,
               mount: str = "smd") -> ExportResult:
    if not symbols_dir.exists():
        raise FileNotFoundError(
            f"KiCad-Symbolbibliothek nicht gefunden ({symbols_dir}). "
            "Ist KiCad installiert?"
        )
    blocks, connections = get_diagram(project_id)
    components = list_components(project_id)
    library = load_library()

    if mount not in ("smd", "tht"):
        raise ValueError(f"mount muss 'smd' oder 'tht' sein, nicht {mount!r}")
    model = build_export_model(blocks, connections, components, library, mount=mount)
    schematic = write_schematic(model, symbols_dir, project_id)

    report = {
        "instances": [
            {"ref": i.ref, "name": i.name, "value": i.value,
             "block": i.block_name, "status": i.status, "footprint": i.footprint}
            for i in model.instances
        ],
        "unmapped": model.unmapped,
        "warnings": model.warnings,
        "counts": {
            "mapped": sum(1 for i in model.instances if i.status == "mapped"),
            "fallback": sum(1 for i in model.instances if i.status == "fallback"),
            "unverified": sum(1 for i in model.instances if i.status == "unverified"),
            "unmapped": len(model.unmapped),
            "no_footprint": sum(1 for i in model.instances if not i.footprint),
        },
    }
    return ExportResult(schematic_text=schematic, report=report)
