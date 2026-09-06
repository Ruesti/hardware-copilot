from pathlib import Path

from .conftest import requires_kicad, run_erc

FIXTURE = Path(__file__).parent / "fixtures" / "minimal.kicad_sch"


@requires_kicad
def test_minimal_schematic_passes_erc(tmp_path):
    target = tmp_path / "minimal.kicad_sch"
    target.write_text(FIXTURE.read_text())
    errors, report = run_erc(target)
    assert errors == 0, report
