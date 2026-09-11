"""PCB-Erzeugung: Export-Modell → Platzierungs-JSON → pcbnew-Subprozess.

Die Bauteile werden wie im Schaltplan nach Funktionsblöcken gruppiert
(Spalte je Block, ICs links, Passive rechts), die Pads tragen die Netze aus
dem Export-Modell — KiCad zeigt damit sofort die Luftlinien (Ratsnest).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .modell import ExportModel

SCRIPT = Path(__file__).resolve().parent / "pcb_build_script.py"
SYSTEM_PYTHON = "/usr/bin/python3"

COL_WIDTH = 60.0
IC_X_OFF = 15.0
PASSIVE_X_OFF = 42.0
ROW_TOP = 25.0
IC_STEP = 35.0
PASSIVE_STEP = 10.0
MARGIN = 8.0


def pcbnew_available() -> bool:
    if not Path(SYSTEM_PYTHON).exists():
        return False
    probe = subprocess.run(
        [SYSTEM_PYTHON, "-c", "import pcbnew"], capture_output=True, timeout=60,
    )
    return probe.returncode == 0


def build_pcb(model: ExportModel, out_path: Path) -> list[dict]:
    """Schreibt die .kicad_pcb; gibt Liste übersprungener Bauteile zurück."""
    instances = []
    texts = []
    blocks_in_order: list[str] = []
    for inst in model.instances:
        if inst.block_name not in blocks_in_order:
            blocks_in_order.append(inst.block_name)

    skipped_no_fp = []
    max_y = ROW_TOP
    max_x = 20.0
    for col, block_name in enumerate(blocks_in_order):
        x_base = 20.0 + col * COL_WIDTH
        texts.append({"text": block_name, "x": x_base + 5, "y": ROW_TOP - 8})
        ic_y = ROW_TOP
        passive_y = ROW_TOP
        for inst in model.instances:
            if inst.block_name != block_name:
                continue
            if not inst.footprint:
                skipped_no_fp.append({
                    "ref": inst.ref, "footprint": "",
                    "reason": "kein Footprint zugeordnet",
                })
                continue
            is_passive = inst.lib_id.startswith(("Device:", "Diode:"))
            if is_passive:
                x, y = x_base + PASSIVE_X_OFF, passive_y
                passive_y += PASSIVE_STEP
            else:
                x, y = x_base + IC_X_OFF, ic_y
                ic_y += IC_STEP
            instances.append({
                "ref": inst.ref, "value": inst.value, "footprint": inst.footprint,
                "x": x, "y": y, "pads": inst.pin_nets,
            })
            max_y = max(max_y, ic_y, passive_y)
        max_x = max(max_x, x_base + COL_WIDTH)

    payload = {
        "instances": instances,
        "texts": texts,
        "outline": {
            "x0": 20.0 - MARGIN, "y0": ROW_TOP - 15.0,
            "x1": max_x, "y1": max_y + MARGIN,
        },
    }

    proc = subprocess.run(
        [SYSTEM_PYTHON, str(SCRIPT), str(out_path)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"PCB-Erzeugung fehlgeschlagen: {proc.stderr.strip()[:500]}")
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    return skipped_no_fp + result.get("skipped", [])


def render_pcb(model: ExportModel) -> tuple[bytes, list[dict]]:
    """Erzeugt die Board-Datei in einem Temp-Verzeichnis und liefert die Bytes."""
    if not pcbnew_available():
        raise FileNotFoundError(
            "pcbnew-Python nicht verfügbar — ist KiCad installiert?"
        )
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "board.kicad_pcb"
        skipped = build_pcb(model, out)
        return out.read_bytes(), skipped
