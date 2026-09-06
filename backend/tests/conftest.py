import re
import shutil
import subprocess
from pathlib import Path

import pytest

KICAD_SYMBOLS = Path("/usr/share/kicad/symbols")
HAS_KICAD_CLI = shutil.which("kicad-cli") is not None

requires_kicad = pytest.mark.skipif(
    not (KICAD_SYMBOLS.exists() and HAS_KICAD_CLI),
    reason="KiCad nicht installiert",
)


def run_erc(sch_path: Path) -> tuple[int, str]:
    """Führt kicad-cli sch erc aus; gibt (Anzahl Fehler-Verstöße, Diagnosetext) zurück.

    JSON-Report statt Textreport, damit das Ergebnis unabhängig von der
    KiCad-Oberflächensprache auswertbar ist. -1 = Datei ließ sich nicht laden.
    """
    import json

    report = sch_path.with_suffix(".json")
    proc = subprocess.run(
        ["kicad-cli", "sch", "erc", "--output", str(report), "--format", "json",
         "--severity-error", "--exit-code-violations", str(sch_path)],
        capture_output=True, text=True, timeout=120,
    )
    if not report.exists():
        return -1, (
            f"kicad-cli rc={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    data = json.loads(report.read_text())
    violations = [v for sheet in data.get("sheets", []) for v in sheet.get("violations", [])]
    text = json.dumps(violations, indent=2, ensure_ascii=False)
    return len(violations), text
