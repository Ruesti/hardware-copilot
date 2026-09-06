# KiCad-Export Etappe 5.1 — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `GET /projects/{id}/export/kicad` liefert eine self-contained `.kicad_sch` (KiCad 9), die fehlerfrei öffnet und deren ERC keine Fehler meldet — Pin-Fakten aus kuratierter Bibliothek, Netz-Semantik aus `net_role`/Verbindungen.

**Architecture:** Kuratiertes `parts.yaml` mappt MPN → KiCad-Symbol + Rollen-Pins. `netlist.py` leitet deterministisch Netznamen ab (conn_type, Pin-Rollen, `net_role`). `sch_writer.py` schreibt S-Expressions mit eingebetteten Symbolen aus `/usr/share/kicad/symbols/`. `kicad-cli sch erc` ist das Test-Orakel.

**Tech Stack:** Python 3.13, FastAPI, SQLite, PyYAML (vorhanden), pytest (neu), kicad-cli 9.0.2 (NUC), React/TS (nur Task 9).

**Spec:** `docs/superpowers/specs/2026-09-06-kicad-export-design.md`

## Global Constraints

- Zielformat: KiCad 9 (`kicad-cli version` → 9.0.2 auf dem NUC); Symbolquelle `/usr/share/kicad/symbols/`.
- Erzeugte Datei muss self-contained sein (alle Symbole in `lib_symbols` eingebettet).
- Keine erfundenen Pin-Fakten: jede `role_to_pin`-Angabe wird per Test gegen das echte KiCad-Symbol geprüft; KiCad-Symbole gelten als verifizierte Pin-Quelle.
- UUIDs deterministisch: `uuid.uuid5(EXPORT_NS, <db-id>)` mit `EXPORT_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")` (Namespace-DNS-Konstante genügt; einmal in `sch_writer.py` definiert).
- Tests, die KiCad brauchen: `pytest.mark.skipif(not Path("/usr/share/kicad/symbols").exists(), reason="KiCad nicht installiert")` bzw. `shutil.which("kicad-cli") is None`.
- Alle Backend-Kommandos aus `backend/` mit `.venv/bin/python -m pytest` ausführen.
- Commits auf Branch `feat/kicad-export`, Nachrichten Deutsch, Co-Authored-By-Trailer wie in diesem Repo üblich.

---

### Task 1: Branch, pytest-Gerüst, Format-Spike

**Files:**
- Create: `backend/requirements-dev.txt`, `backend/pytest.ini`, `backend/tests/__init__.py`, `backend/tests/conftest.py`, `backend/tests/fixtures/minimal.kicad_sch`, `backend/tests/test_format_spike.py`

**Interfaces:**
- Produces: pytest lauffähig; Marker `requires_kicad`; bestätigte Formatversion (`version`-Zahl) für alle späteren Tasks; ERC-Helper `run_erc(path) -> tuple[int, str]` in `conftest.py`.

- [ ] **Step 1: Branch anlegen**

```bash
git checkout -b feat/kicad-export
```

- [ ] **Step 2: pytest-Setup schreiben**

`backend/requirements-dev.txt`:
```
pytest==8.*
```
`backend/pytest.ini`:
```ini
[pytest]
testpaths = tests
markers =
    requires_kicad: braucht installiertes KiCad (Symbole und/oder kicad-cli)
```
`backend/tests/conftest.py`:
```python
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
    """Führt kicad-cli sch erc aus; gibt (Anzahl Fehler, Reporttext) zurück."""
    report = sch_path.with_suffix(".rpt")
    subprocess.run(
        ["kicad-cli", "sch", "erc", "--output", str(report),
         "--severity-error", "--exit-code-violations", str(sch_path)],
        capture_output=True, text=True, timeout=120,
    )
    text = report.read_text() if report.exists() else ""
    # kicad-cli schreibt "Found N violations" ans Ende des Reports
    import re
    m = re.search(r"Found (\d+) violations?", text)
    errors = int(m.group(1)) if m else -1
    return errors, text
```
```bash
cd backend && .venv/bin/pip install -r requirements-dev.txt
```

- [ ] **Step 3: Failing Test — Minimaldatei besteht ERC**

`backend/tests/test_format_spike.py`:
```python
from pathlib import Path

from .conftest import requires_kicad, run_erc

FIXTURE = Path(__file__).parent / "fixtures" / "minimal.kicad_sch"


@requires_kicad
def test_minimal_schematic_passes_erc(tmp_path):
    target = tmp_path / "minimal.kicad_sch"
    target.write_text(FIXTURE.read_text())
    errors, report = run_erc(target)
    assert errors == 0, report
```
Run: `.venv/bin/python -m pytest tests/test_format_spike.py -v` → FAIL (Fixture fehlt).

- [ ] **Step 4: Minimal-Fixture handschreiben**

`backend/tests/fixtures/minimal.kicad_sch` — ein `Device:R` mit zwei globalen Labels. Grundgerüst (Version ggf. anpassen, siehe Step 5):
```
(kicad_sch (version 20250114) (generator "hardware_copilot") (generator_version "9.0")
  (uuid "11111111-1111-5111-8111-111111111111")
  (paper "A4")
  (lib_symbols
    <hier die komplette Symboldefinition "Device:R" aus /usr/share/kicad/symbols/Device.kicad_sym,
     Block (symbol "R" ...) inkl. Untersymbole, mit lib_id-Präfix: (symbol "Device:R" ...)>
  )
  (symbol (lib_id "Device:R") (at 127 63.5 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid "22222222-2222-5222-8222-222222222222")
    (property "Reference" "R1" (at 129 62 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at 129 65 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0402_1005Metric" (at 127 63.5 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "32222222-2222-5222-8222-222222222222"))
    (pin "2" (uuid "42222222-2222-5222-8222-222222222222"))
    (instances (project "export" (path "/11111111-1111-5111-8111-111111111111" (reference "R1") (unit 1))))
  )
  (global_label "3V3" (shape input) (at 127 59.69 90) (effects (font (size 1.27 1.27)))
    (uuid "52222222-2222-5222-8222-222222222222"))
  (global_label "GND" (shape input) (at 127 67.31 270) (effects (font (size 1.27 1.27)))
    (uuid "62222222-2222-5222-8222-222222222222"))
  (sheet_instances (path "/" (page "1")))
)
```
Wichtig: `Device:R` ist 7,62 mm lang (Pin 1 bei y−3,81, Pin 2 bei y+3,81 relativ zur Instanz) — Labels exakt auf die Pin-Enden setzen, sonst meldet ERC „label not connected".

- [ ] **Step 5: Formatversion gegen installiertes KiCad prüfen**

Referenz suchen und Version der Fixture daran angleichen:
```bash
dpkg -L kicad 2>/dev/null | grep -i demos | head -3
grep -rho "(version [0-9]*)" /usr/share/kicad/demos/**/*.kicad_sch 2>/dev/null | sort -u | head -3
```
Falls keine Demos installiert: Fixture-Version `20250114` belassen und Step 6 entscheiden lassen (ERC-Fehlermeldung nennt bei Format-Problemen die erwartete Version).

- [ ] **Step 6: Test grün bekommen**

Run: `.venv/bin/python -m pytest tests/test_format_spike.py -v`
Expected: PASS. Bei FAIL: Report lesen (`assert`-Ausgabe), Fixture iterieren — genau dafür ist der Spike da. Die final funktionierende Struktur ist die verbindliche Vorlage für `sch_writer.py` (Task 6).

- [ ] **Step 7: Commit**

```bash
git add backend/requirements-dev.txt backend/pytest.ini backend/tests/
git commit -m "KiCad-Export 5.1: pytest-Gerüst + Format-Spike (ERC-validierte Minimaldatei)"
```

---

### Task 2: Bauteil-Bibliothek `parts.yaml` + Loader

**Files:**
- Create: `backend/library/parts.yaml`, `backend/app/kicad/__init__.py`, `backend/app/kicad/library.py`, `backend/tests/test_library.py`

**Interfaces:**
- Produces: `load_library() -> Library`; `Library.for_component(mpn: str | None, comp_type: str | None) -> LibraryPart | None`; `LibraryPart(lib_id: str, footprint: str, role_to_pin: dict[str, list[str]], validated: bool)`; Rollen-Vokabular (s. u.).

**Rollen-Vokabular** (verbindlich für Tasks 4–6): `VDD`, `GND`, `SDA`, `SCL`, `SPI_CLK`, `SPI_MOSI`, `SPI_MISO`, `SPI_CS`, `USB_DP`, `USB_DN`, `VBUS`, `VBAT`, `VOUT`, `VIN`, `EN`, `STAT`, `PROG`, `CC1`, `CC2`, `P1`, `P2` (Zweipoler).

- [ ] **Step 1: Failing Tests**

`backend/tests/test_library.py`:
```python
from app.kicad.library import load_library


def test_load_library_has_mcp73831():
    lib = load_library()
    part = lib.for_component("MCP73831T-2ACI/OT", "power_ic")
    assert part is not None
    assert part.lib_id == "Battery_Management:MCP73831-2-OT"
    assert part.role_to_pin["VBAT"] == ["3"]  # Datenblatt DS20001984H, Package Types
    assert part.role_to_pin["VDD"] == ["4"]
    assert part.validated is True


def test_type_fallback_resistor():
    lib = load_library()
    part = lib.for_component("RC0402FR-0710KL-UNBEKANNT", "passive_resistor")
    # unbekannte MPN → Typ-Fallback
    assert part.lib_id == "Device:R"
    assert part.role_to_pin == {"P1": ["1"], "P2": ["2"]}


def test_unknown_component_returns_none():
    lib = load_library()
    assert lib.for_component("GIBTSNICHT-123", "exotic_ic") is None
```
Run: `.venv/bin/python -m pytest tests/test_library.py -v` → FAIL (Modul fehlt).

- [ ] **Step 2: `parts.yaml` schreiben**

Struktur:
```yaml
# Kuratierte Bauteil-Bibliothek. Pin-Nummern stammen aus den offiziellen
# KiCad-9-Symbolen (Community-reviewt); role_to_pin wird per Test gegen das
# Symbol geprüft (test_library_symbols.py).
parts:
  "MCP73831T-2ACI/OT":
    lib_id: "Battery_Management:MCP73831-2-OT"
    footprint: "Package_TO_SOT_SMD:SOT-23-5"
    datasheet: "https://ww1.microchip.com/downloads/en/DeviceDoc/MCP73831-Family-Data-Sheet-DS20001984H.pdf"
    validated: true
    role_to_pin: {STAT: ["1"], GND: ["2"], VBAT: ["3"], VDD: ["4"], PROG: ["5"]}
  "SHT31-DIS-B":
    lib_id: "Sensor_Humidity:SHT31-DIS"
    footprint: "Package_DFN_QFN:Sensirion_DFN-8-1EP_2.5x2.5mm_P0.5mm_EP1.1x1.7mm"
    validated: true
    role_to_pin: {}   # in Step 4 aus dem Symbol befüllen
  # … analog: ESP32-S3-WROOM-1-N8 (RF_Module:ESP32-S3-WROOM-1),
  # XC6220A331MR-G (Regulator_Linear:XC6220B331MR),
  # USB4135-GF-A (Connector:USB_C_Receptacle_USB2.0_16P),
  # DM3AT-SF-PEJM5 (Connector:Micro_SD_Card_Det1),
  # S2B-PH-K-S (Connector:Conn_01x02_Pin),
  # ESD5Z5.0T1G (Diode:ESD5Zxx)
type_fallbacks:
  passive_resistor:  {lib_id: "Device:R", footprint: "", role_to_pin: {P1: ["1"], P2: ["2"]}}
  passive_capacitor: {lib_id: "Device:C", footprint: "", role_to_pin: {P1: ["1"], P2: ["2"]}}
  protection:        {lib_id: "Diode:ESD5Zxx", footprint: "", role_to_pin: {P1: ["1"], P2: ["2"]}}
```

- [ ] **Step 3: Loader implementieren**

`backend/app/kicad/library.py`:
```python
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


def _to_part(raw: dict) -> LibraryPart:
    return LibraryPart(
        lib_id=raw["lib_id"],
        footprint=raw.get("footprint", ""),
        role_to_pin={k: [str(p) for p in v] for k, v in raw.get("role_to_pin", {}).items()},
        validated=bool(raw.get("validated", False)),
        datasheet=raw.get("datasheet", ""),
    )


def load_library(path: Path = LIBRARY_PATH) -> Library:
    data = yaml.safe_load(path.read_text())
    return Library(
        parts={mpn: _to_part(raw) for mpn, raw in (data.get("parts") or {}).items()},
        type_fallbacks={t: _to_part(raw) for t, raw in (data.get("type_fallbacks") or {}).items()},
    )
```
Run: `.venv/bin/python -m pytest tests/test_library.py -v` → die zwei ersten Tests je nach YAML-Füllstand; `test_load_library_has_mcp73831` muss PASS sein.

- [ ] **Step 4: Pin-Namen der Symbole dumpen und alle 8 role_to_pin-Maps ausfüllen**

Für jedes Symbol die echten Pins ansehen (Nummer + Name), z. B.:
```bash
python3 - <<'EOF'
import re, pathlib
for lib, sym in [("RF_Module","ESP32-S3-WROOM-1"),("Sensor_Humidity","SHT31-DIS"),
                 ("Regulator_Linear","XC6220B331MR"),("Connector","USB_C_Receptacle_USB2.0_16P"),
                 ("Connector","Micro_SD_Card_Det1"),("Connector","Conn_01x02_Pin"),("Diode","ESD5Zxx")]:
    text = pathlib.Path(f"/usr/share/kicad/symbols/{lib}.kicad_sym").read_text()
    # naive Pin-Liste: (pin ... (name "X" ...) ... (number "N" ...))
    block = text[text.index(f'symbol "{sym}"'):]
    pins = re.findall(r'\(name "([^"]+)"[^)]*\).*?\(number "([^"]+)"', block[:40000], re.S)
    print(lib, sym, sorted(set((n, num) for n, num in pins))[:40])
EOF
```
Damit die `role_to_pin`-Maps vervollständigen. Festlegungen (Design-Entscheidungen, im YAML als Kommentar dokumentieren):
- ESP32-S3: `SDA → GPIO8`, `SCL → GPIO9`, `SPI_CLK → GPIO12`, `SPI_MOSI → GPIO11`, `SPI_MISO → GPIO13`, `SPI_CS → GPIO10`, `USB_DP → GPIO20/USB_D+`, `USB_DN → GPIO19/USB_D-` (echte Pin-Nummern aus dem Dump), `VDD → 3V3-Pin`, `GND → alle GND-Pins`, `EN → EN`.
- USB-C-Buchse: `VBUS → A4/B9-Pins`, `GND → A1/B12/S1`, `USB_DP → A6/B6`, `USB_DN → A7/B7`, `CC1/CC2` (Nummern aus Dump).
- Mehrfach-Pins je Rolle sind erlaubt (`list[str]`).

- [ ] **Step 5: Alle Tests grün**

Run: `.venv/bin/python -m pytest tests/test_library.py -v` → 3 PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/library/parts.yaml backend/app/kicad/ backend/tests/test_library.py
git commit -m "KiCad-Export 5.1: kuratierte Bauteil-Bibliothek (8 MPNs + Typ-Fallbacks) mit Loader"
```

---

### Task 3: Symbol-Extraktor (.kicad_sym lesen, Bibliothek kreuzvalidieren)

**Files:**
- Create: `backend/app/kicad/sexpr.py`, `backend/app/kicad/symbols.py`, `backend/tests/test_symbols.py`, `backend/tests/test_library_symbols.py`

**Interfaces:**
- Consumes: `load_library()` (Task 2).
- Produces: `sexpr.parse(text) -> SNode` und `sexpr.dumps(node) -> str` (`SNode = list[str | SNode]`, Atome als str, Strings quoted-markiert via `sexpr.Quoted(str)`); `symbols.extract_symbol(lib_name: str, symbol_name: str, symbols_dir: Path) -> SNode` (löst `extends` auf, benennt in `"<Lib>:<Name>"` um); `symbols.symbol_pins(node) -> list[Pin]` mit `Pin(number: str, name: str, x: float, y: float, rotation: int)`.

- [ ] **Step 1: Failing Tests**

`backend/tests/test_symbols.py`:
```python
from pathlib import Path

from app.kicad import sexpr
from app.kicad.symbols import extract_symbol, symbol_pins
from .conftest import KICAD_SYMBOLS, requires_kicad


def test_sexpr_roundtrip():
    node = sexpr.parse('(a (b "c d") 1.5)')
    assert sexpr.dumps(node).split() == '(a (b "c d") 1.5)'.split()


@requires_kicad
def test_extract_device_r_has_two_pins():
    node = extract_symbol("Device", "R", KICAD_SYMBOLS)
    pins = symbol_pins(node)
    assert sorted(p.number for p in pins) == ["1", "2"]


@requires_kicad
def test_extract_resolves_extends():
    # SHT31-DIS erbt via extends von SHT30-DIS — Extraktion muss Pins liefern
    node = extract_symbol("Sensor_Humidity", "SHT31-DIS", KICAD_SYMBOLS)
    assert len(symbol_pins(node)) >= 8
```
`backend/tests/test_library_symbols.py` (das Sicherheitsnetz gegen erfundene Pins):
```python
from app.kicad.library import load_library
from app.kicad.symbols import extract_symbol, symbol_pins
from .conftest import KICAD_SYMBOLS, requires_kicad


@requires_kicad
def test_every_library_pin_exists_in_symbol():
    lib = load_library()
    all_parts = list(lib.parts.items()) + list(lib.type_fallbacks.items())
    for key, part in all_parts:
        libname, symname = part.lib_id.split(":", 1)
        pins = {p.number for p in symbol_pins(extract_symbol(libname, symname, KICAD_SYMBOLS))}
        for role, numbers in part.role_to_pin.items():
            for n in numbers:
                assert n in pins, f"{key}: Rolle {role} nennt Pin {n}, Symbol hat {sorted(pins)}"
```
Run: `.venv/bin/python -m pytest tests/test_symbols.py tests/test_library_symbols.py -v` → FAIL.

- [ ] **Step 2: S-Expression-Parser implementieren**

`backend/app/kicad/sexpr.py`:
```python
from __future__ import annotations


class Quoted(str):
    """String, der beim Serialisieren in Anführungszeichen steht."""


SNode = list  # rekursiv: list[str | Quoted | SNode]


def parse(text: str) -> SNode:
    tokens = _tokenize(text)
    pos = 0

    def read() -> object:
        nonlocal pos
        tok = tokens[pos]; pos += 1
        if tok == "(":
            node: SNode = []
            while tokens[pos] != ")":
                node.append(read())
            pos += 1
            return node
        if tok.startswith('"'):
            return Quoted(tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        return tok

    return read()


def _tokenize(text: str) -> list[str]:
    tokens, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c in "()":
            tokens.append(c); i += 1
        elif c == '"':
            j = i + 1
            while text[j] != '"' or text[j - 1] == "\\":
                j += 1
            tokens.append(text[i:j + 1]); i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            tokens.append(text[i:j]); i = j
    return tokens


def dumps(node: object, indent: int = 0) -> str:
    if isinstance(node, Quoted):
        return '"' + str(node).replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(node, str):
        return node
    inner = " ".join(dumps(child) for child in node)
    if len(inner) <= 100:
        return f"({inner})"
    pad = "  " * (indent + 1)
    parts = [dumps(node[0])]
    for child in node[1:]:
        parts.append("\n" + pad + dumps(child, indent + 1))
    return "(" + " ".join(parts[:1]) + "".join(parts[1:]) + ")"
```

- [ ] **Step 3: Symbol-Extraktion implementieren**

`backend/app/kicad/symbols.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import sexpr
from .sexpr import Quoted


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    x: float
    y: float
    rotation: int


@lru_cache(maxsize=32)
def _load_lib(path_str: str) -> dict[str, list]:
    doc = sexpr.parse(Path(path_str).read_text())
    out = {}
    for node in doc[1:]:
        if isinstance(node, list) and node and node[0] == "symbol":
            out[str(node[1])] = node
    return out

def extract_symbol(lib_name: str, symbol_name: str, symbols_dir: Path) -> list:
    lib = _load_lib(str(symbols_dir / f"{lib_name}.kicad_sym"))
    if symbol_name not in lib:
        raise KeyError(f"Symbol {symbol_name} nicht in {lib_name}")
    node = _deep_copy(lib[symbol_name])
    parent_name = _extends_target(node)
    if parent_name:
        parent = _deep_copy(lib[parent_name])
        node = _merge_extends(parent, node, symbol_name)
    node[1] = Quoted(f"{lib_name}:{symbol_name}")
    _rename_subsymbols(node, symbol_name, f"{lib_name}:{symbol_name}")
    return node

def _extends_target(node: list) -> str | None:
    for child in node:
        if isinstance(child, list) and child and child[0] == "extends":
            return str(child[1])
    return None

def _merge_extends(parent: list, child: list, child_name: str) -> list:
    # Kind übernimmt Grafik/Pins vom Parent, behält eigene Properties
    child_props = [c for c in child if isinstance(c, list) and c and c[0] == "property"]
    merged = [c for c in parent if not (isinstance(c, list) and c and c[0] == "property")]
    insert_at = 2
    for prop in reversed(child_props):
        merged.insert(insert_at, prop)
    return merged

def _rename_subsymbols(node: list, old_prefix: str, new_prefix: str) -> None:
    for child in node:
        if isinstance(child, list) and child and child[0] == "symbol":
            child[1] = Quoted(str(child[1]).replace(old_prefix, new_prefix, 1))

def _deep_copy(node):
    return [(_deep_copy(c) if isinstance(c, list) else c) for c in node]

def symbol_pins(node: list) -> list[Pin]:
    pins: list[Pin] = []
    def walk(n):
        for child in n:
            if isinstance(child, list) and child:
                if child[0] == "pin":
                    at = next(c for c in child if isinstance(c, list) and c[0] == "at")
                    name = next(c for c in child if isinstance(c, list) and c[0] == "name")
                    number = next(c for c in child if isinstance(c, list) and c[0] == "number")
                    pins.append(Pin(str(number[1]), str(name[1]), float(at[1]),
                                    float(at[2]), int(float(at[3])) if len(at) > 3 else 0))
                else:
                    walk(child)
    walk(node)
    return pins
```
Hinweis: `_merge_extends` beim Implementieren gegen das echte SHT31-Symbol prüfen (Parent-Untersymbole heißen `SHT30-DIS_x_y` → `_rename_subsymbols` muss nach dem Merge auf den Parent-Prefix angewendet werden). Der Test deckt das ab — bei FAIL Merge-Logik anpassen.

- [ ] **Step 4: Tests grün, dann Task-2-YAML gegen Symbole fixen**

Run: `.venv/bin/python -m pytest tests/test_symbols.py tests/test_library_symbols.py -v`
Expected: PASS. `test_every_library_pin_exists_in_symbol` deckt jeden Tippfehler in `parts.yaml` auf — YAML korrigieren, bis grün.

- [ ] **Step 5: Commit**

```bash
git add backend/app/kicad/sexpr.py backend/app/kicad/symbols.py backend/tests/test_symbols.py backend/tests/test_library_symbols.py backend/library/parts.yaml
git commit -m "KiCad-Export 5.1: S-Expression-Parser + Symbol-Extraktor mit extends-Auflösung; Bibliothek kreuzvalidiert"
```

---

### Task 4: `net_role` an Komponenten (DB, Modelle, KI-Schema)

**Files:**
- Modify: `backend/app/db.py` (Migration), `backend/app/models.py` (Component-Modelle), `backend/app/repository.py` (INSERT/SELECT/UPDATE für components), `backend/app/claude_service.py` (suggest_components-Prompt + Parser)
- Create: `backend/tests/test_net_role.py`

**Interfaces:**
- Produces: `Component.net_role: str | None` überall durchgereicht. Vokabular: `decoupling` | `pullup:<ROLLE>` | `pulldown:<ROLLE>` | `series:<ROLLE>` | `prog_resistor` (ROLLE aus Task-2-Vokabular, z. B. `pullup:SDA`).

- [ ] **Step 1: Failing Test**

`backend/tests/test_net_role.py`:
```python
import os

os.environ.setdefault("HC_DB_PATH", "")  # falls db.py einen Override bekommt — sonst tmp-CWD nutzen


def test_component_net_role_roundtrip(tmp_path, monkeypatch):
    import app.db as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    db.init_db()

    from app.models import ComponentCreate
    from app.repository import create_project_named, create_component, list_components
    prj = create_project_named("t")
    create_component(prj.id, ComponentCreate(
        name="10k", type="passive_resistor", description="Pull-up SDA",
        net_role="pullup:SDA",
    ))
    items = list_components(prj.id)
    assert items[0].net_role == "pullup:SDA"
```
Vorbereitung: In `repository.py` nachsehen, wie das Projekt-Anlege-API heißt (`create_project(...)` o. ä.) und den Test an die echte Signatur anpassen — nicht raten, `grep -n "def create_project" app/repository.py`.
Run: `.venv/bin/python -m pytest tests/test_net_role.py -v` → FAIL.

- [ ] **Step 2: Migration + Modelle + Repository**

`db.py` in `init_db()` bei den bestehenden idempotenten Migrationen ergänzen:
```python
        if not _column_exists(conn, "components", "net_role"):
            conn.execute("ALTER TABLE components ADD COLUMN net_role TEXT")
```
`models.py`: In `Component`, `ComponentCreate`, `ComponentUpdate` jeweils `net_role: str | None = None` ergänzen.
`repository.py`: In den components-SELECTs die Spalte aufnehmen, in INSERT/UPDATE durchreichen (bestehendes Muster der Nachbarfelder wie `mpn` kopieren).

- [ ] **Step 3: KI-Schema erweitern**

In `claude_service.py` im `suggest_components`-Prompt das JSON-Feld dokumentieren (bei den bestehenden Feldbeschreibungen):
```
"net_role": eines von "decoupling" | "pullup:<NETZ>" | "pulldown:<NETZ>" | "series:<NETZ>" | "prog_resistor" | null.
NETZ ist der logische Anschluss, z. B. "pullup:SDA", "series:SPI_CLK", "pulldown:CC1".
Für ICs/Steckverbinder: null.
```
Im Parser (dort, wo die Komponenten-Dicts in `ComponentCreate` überführt werden) `net_role=raw.get("net_role")` durchreichen.

- [ ] **Step 4: Tests grün + alle Alt-Tests**

Run: `.venv/bin/python -m pytest -v`
Expected: alle PASS (Migration ist idempotent, Alt-DBs bekommen die Spalte).

- [ ] **Step 5: Commit**

```bash
git add backend/app/db.py backend/app/models.py backend/app/repository.py backend/app/claude_service.py backend/tests/test_net_role.py
git commit -m "KiCad-Export 5.1: net_role-Feld (DB+Modelle+KI-Schema) — strukturierte Netz-Semantik statt Beschreibungstext"
```

---

### Task 5: Netz-Ableitung (Export-Modell)

**Files:**
- Create: `backend/app/kicad/netlist.py`, `backend/tests/test_netlist.py`

**Interfaces:**
- Consumes: `Library`/`LibraryPart` (Task 2), DB-Modelle (`DiagramBlock`, `BlockConnection`, `Component` mit `net_role`).
- Produces:
```python
@dataclass
class SymbolInstance:
    ref: str                      # "U1", "R3", …
    lib_id: str
    value: str
    footprint: str
    block_name: str
    pin_nets: dict[str, str]      # Pin-Nummer -> Netzname (nur belegte Pins)
    status: str                   # "mapped" | "fallback" | "unverified"

@dataclass
class ExportModel:
    instances: list[SymbolInstance]
    unmapped: list[dict]          # {name, mpn, type, block_name, reason}
    warnings: list[str]

def build_export_model(blocks, connections, components, library) -> ExportModel: ...
```

- [ ] **Step 1: Failing Tests (Kernregeln)**

`backend/tests/test_netlist.py` — mit handgebauten Modell-Objekten (kein DB-Zugriff), u. a.:
```python
def test_power_label_normalization():
    from app.kicad.netlist import normalize_power_net
    assert normalize_power_net("3.3V") == "3V3"
    assert normalize_power_net("VBUS 5V") == "VBUS"
    assert normalize_power_net("VBAT 3.6-4.2V") == "VBAT"
    assert normalize_power_net("12V") == "12V"


def test_i2c_connection_creates_sda_scl_nets(minimal_design):
    # minimal_design: MCU-Block --i2c--> Sensor-Block, beide Teile mit SDA/SCL-Rollen,
    # dazu 2 Pull-up-Widerstände (net_role pullup:SDA / pullup:SCL) im Sensor-Block
    model = build(minimal_design)
    mcu = by_ref(model, "U1"); sensor = by_ref(model, "U2")
    sda_pin_mcu = pin_for_role(mcu, "SDA")      # Helper: über Bibliothek role->pin
    assert mcu.pin_nets[sda_pin_mcu] == "SDA"
    r_pullup = by_value(model, "10kΩ", role="pullup:SDA")
    assert set(r_pullup.pin_nets.values()) == {"SDA", "3V3"}


def test_decoupling_cap_gets_block_supply_and_gnd(minimal_design): ...
def test_unknown_mpn_lands_in_unmapped(minimal_design): ...
def test_gnd_connection_and_vdd_roles(minimal_design): ...
```
(Fixtures als pytest-Fixture `minimal_design` konkret ausschreiben: 2–3 Blöcke, 4–6 Komponenten, 3 Verbindungen — Datenform wie die Pydantic-Modelle.)
Run: → FAIL.

- [ ] **Step 2: Regeln implementieren**

`netlist.py` — Ableitungsregeln in dieser Reihenfolge:
1. **Referenzen vergeben**: Präfix nach Typ (`mcu/power_ic/sensor → U`, `passive_resistor → R`, `passive_capacitor → C`, `connector → J`, `protection → D`), fortlaufend pro Präfix, Reihenfolge = (Block-order, Komponenten-order) → deterministisch.
2. **Blocknetze bestimmen**: je Verbindung `conn_type`:
   - `gnd` → `GND`
   - `i2c` → `SDA`, `SCL`
   - `spi` → `SPI_CLK`, `SPI_MOSI`, `SPI_MISO`, `SPI_CS`
   - `power` → `normalize_power_net(label)`; das Netz wird dem **Zielblock** als `supply_net` zugeordnet (Quelle ist der Versorger), zusätzlich dem Quellblock als Ausgangsnetz (Rolle `VOUT`/`VBUS`/`VBAT`-Pins).
   - `signal` mit Label `USB D+/D-` → `USB_DP`, `USB_DN`.
   `supply_net` eines Blocks = eingehendes power-Netz; MCU/Sensor/microSD im Testprojekt → `3V3`.
3. **IC-/Steckverbinder-Pins belegen**: für jede Rolle in `role_to_pin`, wenn ein zugehöriges Netz am Block anliegt: `VDD → supply_net`, `GND → GND`, Interface-Rollen (`SDA`, `SPI_*`, `USB_*`, `CC1/2`, `VBUS`, `VBAT`, `VOUT`, `VIN`, `EN`, `STAT`, `PROG`) → gleichnamiges Netz, sofern es durch eine Verbindung/Rolle des Blocks entsteht. `EN` ohne eigenes Netz → `supply_net` (Enable = an). Pins ohne ableitbares Netz bleiben unbelegt.
4. **Passive über `net_role`**:
   - `decoupling` → `{P1: supply_net, P2: GND}`
   - `pullup:<R>` → `{P1: <R>, P2: supply_net}`; `pulldown:<R>` → `{P1: <R>, P2: GND}`
   - `series:<R>` → `{P1: <R>, P2: <R>_R<ref>}` (Serien-Element bricht das Netz auf: MCU-Seite `<R>`, Slave-Seite `<R>_R5`-artig) — für 5.1 vereinfachen: beide Seiten benanntes Netz `<R>` und `<R>_S`, dokumentierte Vereinfachung.
   - `prog_resistor` → `{P1: PROG, P2: GND}`
   - ohne `net_role` → Pins unbelegt + Warnung im Modell.
5. **Status**: MPN-Treffer+validated → `mapped`; Typ-Fallback → `fallback`; kein Treffer → `unmapped`-Liste.

- [ ] **Step 3: Tests grün**

Run: `.venv/bin/python -m pytest tests/test_netlist.py -v` → PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/app/kicad/netlist.py backend/tests/test_netlist.py
git commit -m "KiCad-Export 5.1: deterministische Netz-Ableitung (conn_type + Pin-Rollen + net_role) → Export-Modell"
```

---

### Task 6: Schaltplan-Generator (`.kicad_sch` schreiben)

**Files:**
- Create: `backend/app/kicad/sch_writer.py`, `backend/tests/test_sch_writer.py`

**Interfaces:**
- Consumes: `ExportModel` (Task 5), `extract_symbol`/`symbol_pins` (Task 3), Fixture-Struktur aus Task 1.
- Produces: `write_schematic(model: ExportModel, symbols_dir: Path, project_name: str) -> str` (kompletter Dateiinhalt).

- [ ] **Step 1: Failing Tests**

`backend/tests/test_sch_writer.py`:
```python
@requires_kicad
def test_generated_file_passes_erc(tmp_path, demo_export_model):
    text = write_schematic(demo_export_model, KICAD_SYMBOLS, "demo")
    f = tmp_path / "demo.kicad_sch"
    f.write_text(text)
    errors, report = run_erc(f)
    assert errors == 0, report


@requires_kicad
def test_deterministic_output(demo_export_model):
    a = write_schematic(demo_export_model, KICAD_SYMBOLS, "demo")
    b = write_schematic(demo_export_model, KICAD_SYMBOLS, "demo")
    assert a == b


def test_all_instances_and_labels_present(demo_export_model_nosym):
    # ohne KiCad lauffähig: Mini-Symbolverzeichnis als Fixture (Device.kicad_sym-Auszug)
    text = write_schematic(demo_export_model_nosym, FIXTURE_SYMBOLS, "demo")
    assert '"R1"' in text and 'global_label "3V3"' in text
```
`demo_export_model`: kleines ExportModel mit 1× MCP73831 + 2 Kondensatoren + 1 PROG-Widerstand (Netze VBUS/VBAT/GND/PROG) — konkret als Fixture in `conftest.py` ausschreiben.
Run: → FAIL.

- [ ] **Step 2: Generator implementieren**

`sch_writer.py` – Aufbau exakt nach der in Task 1 validierten Fixture-Struktur:
1. Kopf (`kicad_sch`, `version` aus Task-1-Erkenntnis, `generator "hardware_copilot"`, Datei-UUID = `uuid5(EXPORT_NS, project_name)`), `paper "A3"`.
2. `lib_symbols`: `extract_symbol` je einzigartiger `lib_id` des Modells.
3. Platzierung: Blöcke als Spalten/Zeilen-Raster (Blockbreite 80 mm, ICs links, Passive rechts daneben in 10-mm-Raster; alle Koordinaten auf 1,27-mm-Raster runden — KiCad-Anschlusslogik arbeitet auf diesem Raster, sonst treffen Labels die Pins nicht). Blocktitel als `(text "..." …)`.
4. Je Instanz: `(symbol (lib_id …) (at x y 0) …)` mit Properties Reference/Value/Footprint, `pin`-UUID-Liste, `instances`-Block (wie Fixture). UUIDs: `uuid5(EXPORT_NS, f"{ref}")` bzw. `f"{ref}:pin:{nr}"`.
5. Je belegtem Pin: Pin-Position = Instanzposition + rotierte Symbolpin-Koordinate (nur Rotation 0 → Position = `(x_inst + x_pin, y_inst - y_pin)`; KiCad-Y-Achse ist invertiert — mit dem ERC-Test verifizieren) → `(global_label "<NET>" (shape input) (at px py rot) …)` mit Label-Rotation = Pin-Rotation.
6. `sheet_instances` wie Fixture.

- [ ] **Step 3: Tests grün (ERC-Report iterieren)**

Run: `.venv/bin/python -m pytest tests/test_sch_writer.py -v`
ERC-Fehler „label not connected" ⇒ Koordinaten-/Rotationsrechnung fixen — der Report nennt Position und Label. Unbelegte Pins erzeugen ggf. `unconnected`-Meldungen: bei `--severity-error` zählen nur Fehler; falls doch als Fehler gemeldet, pro unbelegtem Pin ein `(no_connect (at px py))` schreiben, außer der Pin ist absichtlich offen zu lassen → dann Warnung dokumentieren.

- [ ] **Step 4: Commit**

```bash
git add backend/app/kicad/sch_writer.py backend/tests/test_sch_writer.py backend/tests/conftest.py
git commit -m "KiCad-Export 5.1: S-Expression-Generator — eingebettete Symbole, Block-Raster, globale Labels, ERC-grün"
```

---

### Task 7: Export-Endpoint

**Files:**
- Modify: `backend/app/main.py` (zwei Routen, Abschnitt nach „Diagram")
- Create: `backend/tests/test_export_endpoint.py`

**Interfaces:**
- Consumes: `build_export_model` (Task 5), `write_schematic` (Task 6), `load_library` (Task 2), Repository-Reads (`get_diagram`, `list_components`).
- Produces: `GET /projects/{id}/export/kicad` → `.kicad_sch` (Content-Disposition attachment); `GET /projects/{id}/export/kicad/report` → JSON `{instances: [{ref, name, status}], unmapped: [...], warnings: [...]}`.

- [ ] **Step 1: Failing Test**

```python
def test_export_endpoint_returns_schematic(seeded_client):
    r = seeded_client.get(f"/projects/{PID}/export/kicad")
    assert r.status_code == 200
    assert r.text.startswith("(kicad_sch")
    assert "attachment" in r.headers["content-disposition"]


def test_export_report(seeded_client):
    r = seeded_client.get(f"/projects/{PID}/export/kicad/report")
    data = r.json()
    assert {"instances", "unmapped", "warnings"} <= set(data)
```
`seeded_client`: FastAPI `TestClient` mit tmp-DB (monkeypatch wie Task 4) und Mini-Projekt-Seed (2 Blöcke, 3 Komponenten, 2 Verbindungen) — als Fixture ausschreiben. Achtung: `main.py` importiert beim Laden `.env`-Logik; Test setzt kein `ANTHROPIC_API_KEY` voraus (Export braucht keins — sicherstellen, dass keine Claude-Importe im Exportpfad liegen).
Run: → FAIL.

- [ ] **Step 2: Routen implementieren**

```python
@app.get("/projects/{project_id}/export/kicad")
def export_kicad(project_id: str) -> Response:
    _require_project(project_id)
    from app.kicad.export import run_export  # dünner Orchestrator, s. u.
    result = run_export(project_id)
    return Response(
        content=result.schematic_text,
        media_type="application/x-kicad-schematic",
        headers={"Content-Disposition": f'attachment; filename="{project_id}.kicad_sch"'},
    )


@app.get("/projects/{project_id}/export/kicad/report")
def export_kicad_report(project_id: str) -> dict:
    _require_project(project_id)
    from app.kicad.export import run_export
    result = run_export(project_id)
    return result.report
```
Dazu `backend/app/kicad/export.py` (Orchestrator ~30 Zeilen): lädt Diagramm+Komponenten+Bibliothek, ruft `build_export_model` + `write_schematic`, baut Report-Dict. (Datei zu „Create" in diesem Task.)

- [ ] **Step 3: Tests grün + Gesamtsuite**

Run: `.venv/bin/python -m pytest -v` → alle PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py backend/app/kicad/export.py backend/tests/test_export_endpoint.py
git commit -m "KiCad-Export 5.1: Export-Endpoint (.kicad_sch-Download + JSON-Report)"
```

---

### Task 8: Bugfix `GET /blocks` liefert `schematic_ascii` nicht

**Files:**
- Modify: `backend/app/repository.py:171` (`list_blocks`)
- Create: `backend/tests/test_blocks_endpoint.py`

**Interfaces:**
- Consumes/Produces: `DesignBlock` hat bereits `schematic_ascii`/`schematic_validated`-Felder (prüfen: `grep -n "class DesignBlock" app/models.py`); nur der SELECT füllt sie nicht.

- [ ] **Step 1: Failing Test** — Block anlegen, `set_block_schematic(...)`, dann `list_blocks(...)`:

```python
def test_list_blocks_includes_schematic(tmp_db):
    from app.repository import create_block, set_block_schematic, list_blocks
    from app.models import DesignBlockCreate
    b = create_block(PID, DesignBlockCreate(name="X", description=""))
    set_block_schematic(PID, b.id, "ASCII")
    got = list_blocks(PID)[0]
    assert got.schematic_ascii == "ASCII"
```
Falls `DesignBlock` die Felder nicht hat: im Modell ergänzen (`schematic_ascii: str | None = None`, `schematic_validated: bool = False`) — Frontend-Typen nicht anfassen.

- [ ] **Step 2: SELECT erweitern** (`schematic_ascii`, `COALESCE(schematic_validated,0)` aufnehmen, im Konstruktor durchreichen — Muster von `get_diagram` kopieren).
- [ ] **Step 3: Tests grün.** Run: `.venv/bin/python -m pytest tests/test_blocks_endpoint.py -v`
- [ ] **Step 4: Commit**

```bash
git add backend/app/repository.py backend/app/models.py backend/tests/test_blocks_endpoint.py
git commit -m "Fix: GET /blocks liefert schematic_ascii/validated mit (list_blocks selektierte die Spalten nicht)"
```

---

### Task 9: UI — Export-Button + Report-Anzeige

**Files:**
- Create: `src/api/export.ts`
- Modify: Workbench-Kopfzeile (Datei per `grep -rn "refresh-design\|Workbench" src/ --include=*.tsx -l` lokalisieren; Button neben den bestehenden Aktionen)

**Interfaces:**
- Consumes: Endpoints aus Task 7. `API_BASE_URL`-Muster aus `src/api/diagram.ts` übernehmen.

- [ ] **Step 1: API-Client**

`src/api/export.ts`:
```typescript
import { API_BASE_URL } from "./config"; // exakten Import aus diagram.ts übernehmen

export interface ExportReport {
  instances: { ref: string; name: string; status: "mapped" | "fallback" | "unverified" }[];
  unmapped: { name: string; mpn: string | null; type: string | null; block_name: string; reason: string }[];
  warnings: string[];
}

export async function fetchExportReport(projectId: string): Promise<ExportReport> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/export/kicad/report`);
  if (!res.ok) throw new Error(`Report fehlgeschlagen: ${res.status}`);
  return res.json();
}

export function kicadDownloadUrl(projectId: string): string {
  return `${API_BASE_URL}/projects/${projectId}/export/kicad`;
}
```

- [ ] **Step 2: Button einbauen** — „KiCad-Export": onClick lädt Report, zeigt ihn in einem einfachen Modal (bestehende Modal-Muster im Projekt suchen und wiederverwenden: Anzahl gemappt/Fallback/ungemappt + Warnliste), darin Button „`.kicad_sch` herunterladen" → `window.open(kicadDownloadUrl(id))`.
- [ ] **Step 3: Build prüfen.** Run: `npm run build` (Repo-Root). Expected: keine TS-Fehler. (Visueller Test später auf pc — NUC ist headless.)
- [ ] **Step 4: Commit**

```bash
git add src/api/export.ts src/
git commit -m "KiCad-Export 5.1: Export-Button mit Mapping-Report im Workbench-Tab"
```

---

### Task 10: End-to-End gegen das Testprojekt + Doku + PR

**Files:**
- Modify: `docs/roadmap/phases.md` (5.1-Status), `README.md` (Feature-Zeile)

- [ ] **Step 1: Echtes Testprojekt exportieren**

```bash
cd backend && (.venv/bin/uvicorn app.main:app --port 8123 &) && sleep 3
curl -s http://127.0.0.1:8123/projects/prj-7c6a7c86/export/kicad -o /tmp/logger.kicad_sch
curl -s http://127.0.0.1:8123/projects/prj-7c6a7c86/export/kicad/report | python3 -m json.tool
kicad-cli sch erc --severity-error --exit-code-violations /tmp/logger.kicad_sch; echo "ERC-Exit: $?"
```
Expected: Report plausibel (8 gemappte ICs/Steckverbinder, Passive als Fallback, `unverified` leer), ERC-Exit 0. Hinweis: Das Testprojekt hat noch keine `net_role`-Werte (Bestandsdaten) → Passive erscheinen mit Warnungen/offenen Pins; optional einmal `refresh-design` laufen lassen (erzeugt `net_role` durch das neue Schema; kostet ~0,10 $).

- [ ] **Step 2: Datei dem User schicken** (SendUserFile, `.kicad_sch` + Report) — Gerätetest in KiCad auf pc/Laptop ist die Abnahme.
- [ ] **Step 3: Doku**: `phases.md` Etappe 5.1 → done mit Datum; README „Current Status" um Export-Zeile ergänzen.
- [ ] **Step 4: Push + Draft-PR**

```bash
git push origin feat/kicad-export
gh pr create --draft --title "Phase 5.1: KiCad-Export (Schaltplan-Gerüst)" --body "…Spec-Link, Testnachweis (pytest grün, ERC-Exit 0), offene Punkte (5.2 Datenblatt-Pipeline)…"
```

---

## Self-Review (durchgeführt)

- **Spec-Abdeckung:** Bibliothek (T2), Kreuzvalidierung gegen Symbole (T3), net_role (T4), Netz-Ableitung inkl. Normalisierung/Fehlerfälle (T5), Generator self-contained + deterministisch + ERC (T6, T1), Endpoint+Report (T7), Bugfix GET /blocks (T8), UI (T9), Abnahme+Doku (T10). Etappe 5.2 bewusst nicht Teil dieses Plans.
- **Platzhalter:** Task-2-YAML lässt 7 `role_to_pin`-Maps offen — kein Platzhalter, sondern expliziter Arbeitsschritt (Step 4) mit Dump-Kommando und Sicherheitsnetz-Test (T3). Fixture-/Merge-Details in T1/T3 sind als Iterationsschritte mit Orakel (ERC/Test) formuliert, weil das exakte KiCad-9-Format nur gegen die Installation verifizierbar ist.
- **Typ-Konsistenz:** `LibraryPart.role_to_pin: dict[str, list[str]]` überall; `run_erc` aus T1 in T6/T10 wiederverwendet; `SymbolInstance.status`-Werte = Report-Statuswerte = TS-Typ in T9.
