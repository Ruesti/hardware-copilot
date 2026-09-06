"""PCB-Erzeugung über pcbnew: DRC als Orakel, Netze an Pads via Ratsnest."""
import json
import subprocess
from pathlib import Path

import pytest

from app.kicad.netlist import ExportModel, SymbolInstance
from app.kicad.pcb import pcbnew_available, render_pcb

from .conftest import HAS_KICAD_CLI

requires_pcbnew = pytest.mark.skipif(
    not (pcbnew_available() and HAS_KICAD_CLI),
    reason="pcbnew/kicad-cli nicht verfügbar",
)


@pytest.fixture()
def charger_pcb_model() -> ExportModel:
    return ExportModel(instances=[
        SymbolInstance(
            ref="U1", lib_id="Battery_Management:MCP73831-2-OT",
            value="MCP73831", footprint="Package_TO_SOT_SMD:SOT-23-5",
            block_name="Lader",
            pin_nets={"1": "STAT", "2": "GND", "3": "VBAT", "4": "VBUS", "5": "PROG"},
            status="mapped",
        ),
        SymbolInstance(
            ref="C1", lib_id="Device:C", value="4.7µF",
            footprint="Capacitor_SMD:C_0805_2012Metric", block_name="Lader",
            pin_nets={"1": "VBUS", "2": "GND"}, status="fallback",
        ),
        SymbolInstance(
            ref="R1", lib_id="Device:R", value="2kΩ",
            footprint="Resistor_SMD:R_0402_1005Metric", block_name="Lader",
            pin_nets={"1": "PROG", "2": "GND"}, status="fallback",
        ),
        SymbolInstance(  # ohne Footprint → muss übersprungen werden
            ref="J1", lib_id="Connector:Conn_01x02_Pin", value="X",
            footprint="", block_name="Lader", pin_nets={}, status="fallback",
        ),
    ])


def _drc(pcb_path: Path) -> dict:
    report = pcb_path.with_suffix(".json")
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "--output", str(report), "--format", "json",
         "--severity-error", str(pcb_path)],
        capture_output=True, timeout=120,
    )
    return json.loads(report.read_text())


@requires_pcbnew
def test_pcb_loads_and_passes_drc(tmp_path, charger_pcb_model):
    pcb_bytes, skipped = render_pcb(charger_pcb_model)
    assert [s["ref"] for s in skipped] == ["J1"]
    f = tmp_path / "board.kicad_pcb"
    f.write_bytes(pcb_bytes)
    report = _drc(f)
    violations = report.get("violations", [])
    assert violations == [], violations
    # Netze an den Pads: GND teilen sich U1/C1/R1 → Ratsnest vorhanden
    assert len(report.get("unconnected_items", [])) > 0
