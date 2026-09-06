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


def _load_model(project_id: str, mount: str):
    if mount not in ("smd", "tht"):
        raise ValueError(f"mount muss 'smd' oder 'tht' sein, nicht {mount!r}")
    blocks, connections = get_diagram(project_id)
    components = list_components(project_id)
    library = load_library()
    return build_export_model(blocks, connections, components, library, mount=mount)


def project_slug(project_id: str) -> str:
    import re
    from app.repository import get_project
    project = get_project(project_id)
    name = (project.name if project else project_id) or project_id
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or project_id
    return slug


def run_export(project_id: str, symbols_dir: Path = DEFAULT_SYMBOLS_DIR,
               mount: str = "smd") -> ExportResult:
    if not symbols_dir.exists():
        raise FileNotFoundError(
            f"KiCad-Symbolbibliothek nicht gefunden ({symbols_dir}). "
            "Ist KiCad installiert?"
        )
    model = _load_model(project_id, mount)
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


def run_pcb(project_id: str, mount: str = "smd") -> tuple[bytes, list[dict]]:
    """Erzeugt die .kicad_pcb (Bauteile in Blockgruppen, Netze an den Pads)."""
    from .pcb import render_pcb
    model = _load_model(project_id, mount)
    return render_pcb(model)


def run_open(project_id: str, mount: str = "smd") -> dict:
    """Schreibt Projektdateien (sch, pcb, pro) und öffnet sie in KiCad.

    Auf Rechnern ohne Display/KiCad-GUI werden nur die Dateien geschrieben —
    die Antwort sagt ehrlich, was passiert ist.
    """
    import json
    import os
    import shutil
    import subprocess

    slug = project_slug(project_id)
    result = run_export(project_id, mount=mount)
    target = Path.home() / "HardwareCopilot" / slug
    target.mkdir(parents=True, exist_ok=True)
    sch = target / f"{slug}.kicad_sch"
    sch.write_text(result.schematic_text)
    pro = target / f"{slug}.kicad_pro"
    if not pro.exists():
        pro.write_text(json.dumps({
            "meta": {"filename": pro.name, "version": 3},
            # DRC-Grenzen leben in der Projektdatei: 0,2-mm-Bohrungen erlauben
            # (Thermal-Vias der Module; Standard bei allen gängigen Fertigern)
            "board": {"design_settings": {"rules": {
                "min_through_hole_diameter": 0.2,
                "min_hole_clearance": 0.25,
            }}},
        }, indent=2))

    from .guide import build_guide_html
    model = _load_model(project_id, mount)
    (target / "routing-anleitung.html").write_text(
        build_guide_html(model, slug), encoding="utf-8")

    pcb_note = None
    try:
        pcb_bytes, _skipped = run_pcb(project_id, mount=mount)
        (target / f"{slug}.kicad_pcb").write_bytes(pcb_bytes)
    except Exception as exc:  # PCB ist optional — Schaltplan zählt
        pcb_note = f"PCB nicht erzeugt: {exc}"

    opened = False
    reason = None
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    kicad_bin = shutil.which("kicad")
    if not has_display:
        reason = "kein Display auf diesem Rechner — Dateien wurden nur gespeichert"
    elif not kicad_bin:
        reason = "KiCad-Programm nicht gefunden — Dateien wurden nur gespeichert"
    else:
        subprocess.Popen([kicad_bin, str(pro)], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opened = True

    return {
        "path": str(target), "opened": opened, "reason": reason,
        "pcbNote": pcb_note,
        "files": sorted(f.name for f in target.iterdir()),
    }


def run_guide(project_id: str, mount: str = "smd") -> str:
    """Routing-Anleitung (HTML mit Niveau-Umschalter) für dieses Projekt."""
    from .guide import build_guide_html
    model = _load_model(project_id, mount)
    return build_guide_html(model, project_slug(project_id))
