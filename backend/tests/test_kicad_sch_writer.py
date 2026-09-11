"""Generator-Tests: ERC als Wahrheitsinstanz, Determinismus, Struktur."""
import pytest

from backend.app.kicad.modell import ExportModel, SymbolInstance
from backend.app.kicad.sch_writer import write_schematic

from .kicad_conftest import KICAD_SYMBOLS, requires_kicad, run_erc


@pytest.fixture()
def charger_model() -> ExportModel:
    """MCP73831-Ladeschaltung: IC + 2 Kondensatoren + PROG-Widerstand."""
    return ExportModel(instances=[
        SymbolInstance(
            ref="U1", lib_id="Battery_Management:MCP73831-2-OT",
            value="MCP73831T-2ACI/OT", footprint="Package_TO_SOT_SMD:SOT-23-5",
            block_name="Lademanagement",
            pin_nets={"1": "STAT", "2": "GND", "3": "VBAT", "4": "VBUS", "5": "PROG"},
            status="mapped",
        ),
        SymbolInstance(
            ref="C1", lib_id="Device:C", value="4.7µF", footprint="",
            block_name="Lademanagement",
            pin_nets={"1": "VBUS", "2": "GND"}, status="fallback",
        ),
        SymbolInstance(
            ref="C2", lib_id="Device:C", value="4.7µF", footprint="",
            block_name="Lademanagement",
            pin_nets={"1": "VBAT", "2": "GND"}, status="fallback",
        ),
        SymbolInstance(
            ref="R1", lib_id="Device:R", value="2kΩ", footprint="",
            block_name="Lademanagement",
            pin_nets={"1": "PROG", "2": "GND"}, status="fallback",
        ),
        SymbolInstance(
            ref="R2", lib_id="Device:R", value="10kΩ", footprint="",
            block_name="Lademanagement",
            pin_nets={"1": "STAT", "2": "VBAT"}, status="fallback",
        ),
    ])


@requires_kicad
def test_generated_file_passes_erc(tmp_path, charger_model):
    text = write_schematic(charger_model, KICAD_SYMBOLS, "demo")
    f = tmp_path / "demo.kicad_sch"
    f.write_text(text)
    errors, report = run_erc(f)
    assert errors == 0, report


@requires_kicad
def test_deterministic_output(charger_model):
    a = write_schematic(charger_model, KICAD_SYMBOLS, "demo")
    b = write_schematic(charger_model, KICAD_SYMBOLS, "demo")
    assert a == b


@requires_kicad
def test_structure_contains_instances_and_labels(charger_model):
    import re
    text = write_schematic(charger_model, KICAD_SYMBOLS, "demo")
    assert text.startswith("(kicad_sch (version 20250114)")
    assert '"U1"' in text and '"C2"' in text
    assert '(label "PROG"' in text and '(label "VBAT"' in text
    # Symbol nur einmal eingebettet, auch wenn 2x C verwendet
    assert len(re.findall(r'\(symbol\s+"Device:C"', text)) == 1
    # Blocktitel vorhanden
    assert '(text "Lademanagement"' in text
    # VBUS kommt vom (nicht vorhandenen) Connector -> PWR_FLAG erwartet
    assert "PWR_FLAG" in text


@requires_kicad
def test_stub_wires_present(charger_model):
    import re
    text = write_schematic(charger_model, KICAD_SYMBOLS, "demo")
    wires = re.findall(r"\(wire \(pts", text)
    labels = re.findall(r'\(label "', text)
    assert len(wires) == len(labels), "jeder Label-Punkt hat genau einen Stummel-Draht"
    assert len(wires) > 0
