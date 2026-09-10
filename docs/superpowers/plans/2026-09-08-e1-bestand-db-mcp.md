# E1: Bestands-DB + Bestand-MCP — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SQLite-Bestandsdatenbank plus MCP-Server `bestand` mit sechs Werkzeugen, sodass Claude Code im Terminal Bestandsfragen beantworten kann („Welchen 10-µF-Kondensator habe ich?").

**Architecture:** Neues Python-Paket `bestand/` im hardware-copilot-Repo, Bauart exakt wie `wissensschicht/`: dünner MCP-Layer (`server.py`) → Dienst-Klasse (`service.py`) → kleine Fachmodule (`db.py`, `format.py`, `regal.py`). Die DB-Datei ist die einzige Wahrheit; Pfad kommt per Umgebungsvariable. Spec: `docs/superpowers/specs/2026-09-08-cockpit-bestand-leuchtregal-design.md` (§3.1, §3.2, E1).

**Tech Stack:** Python ≥ 3.11, sqlite3 + urllib (Standardbibliothek), MCP-SDK `mcp>=2,<3`, pytest.

## Global Constraints

- Python ≥ 3.11; MCP-SDK 2.x — **Achtung:** die Server-Klasse heißt dort `MCPServer` und liegt in `mcp.server.mcpserver` (nicht FastMCP).
- Keine neuen Abhängigkeiten: DB über `sqlite3`, HTTP über `urllib` (beides Standardbibliothek).
- Alle Bezeichner, Docstrings, Meldungen und Tests auf Deutsch (Stil von `wissensschicht/`).
- Preise werden **nie ohne Datum** ausgegeben — jede Preiszeile trägt „Stand vom <datum>" (Spec §6).
- DB-Pfad nie hart verdrahtet: Umgebungsvariable `BESTAND_DB`, Default `~/.hardware-copilot/bestand.db`; Tests nutzen `tmp_path`.
- `bestand/` importiert nichts aus `wissensschicht/` und umgekehrt — zwei eigenständige Server.
- Tabellen `projekte`/`verbrauch` sind E5+ und werden hier NICHT angelegt (YAGNI, Spec §5).
- Testlauf immer vom Repo-Wurzelverzeichnis (des Worktrees) mit dem venv des Haupt-Checkouts: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/ -v` — dort sind `mcp` und `pytest` schon installiert.

---

### Task 1: DB-Schicht (`bestand/db.py`)

**Files:**
- Create: `bestand/__init__.py` (leer)
- Create: `bestand/db.py`
- Create: `bestand/tests/__init__.py` (leer)
- Test: `bestand/tests/test_db.py`

**Interfaces:**
- Consumes: —
- Produces: `verbinde(pfad: Path | str) -> sqlite3.Connection` — legt fehlende Tabellen an (idempotent), `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`. Tabellen: `faecher(id, regal, position, led_nummer, UNIQUE(regal, position))`, `teile(id, bezeichnung, hersteller_nr, klasse, menge CHECK >= 0, eckdaten, datenblatt_url, fach_id, angelegt_am)`, `alternativen(id, teil_id, bezeichnung, hersteller_nr, hinweis, datum)`, `preis_cache(id, teil_id, quelle, preis_eur, url, datum)`.

- [ ] **Step 1: Failing Test schreiben**

```python
"""DB-Schicht: Schema anlegen, idempotent, Invarianten der Tabellen."""
import sqlite3

import pytest

from bestand.db import verbinde


def test_verbinde_legt_alle_tabellen_an(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    tabellen = {z["name"] for z in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"teile", "faecher", "alternativen", "preis_cache"} <= tabellen
    assert "projekte" not in tabellen  # E5+, bewusst nicht in E1


def test_verbinde_ist_idempotent_und_erhaelt_daten(tmp_path):
    pfad = tmp_path / "bestand.db"
    conn = verbinde(pfad)
    conn.execute("INSERT INTO faecher (regal, position) VALUES ('A', '3')")
    conn.commit()
    conn.close()

    conn2 = verbinde(pfad)
    zeile = conn2.execute("SELECT regal, position FROM faecher").fetchone()
    assert (zeile["regal"], zeile["position"]) == ("A", "3")


def test_menge_darf_nicht_negativ_werden(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO teile (bezeichnung, menge, angelegt_am)"
                     " VALUES ('X', -1, '2026-09-08')")


def test_fach_ist_je_regal_und_position_eindeutig(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")
    conn.execute("INSERT INTO faecher (regal, position) VALUES ('A', '3')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO faecher (regal, position) VALUES ('A', '3')")
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_db.py -v`
Expected: FAIL / ERROR mit `ModuleNotFoundError: No module named 'bestand.db'`

- [ ] **Step 3: Implementierung**

`bestand/__init__.py` und `bestand/tests/__init__.py`: leere Dateien.

`bestand/db.py`:

```python
"""Bestands-DB: SQLite-Schema anlegen und Verbindung liefern (Spec §3.1, Etappe E1).

Die DB-Datei ist die einzige Wahrheit (Spec §6); der Pfad kommt vom Aufrufer
(MCP-Server: Umgebungsvariable BESTAND_DB). projekte/verbrauch folgen erst in E5+.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS faecher (
    id INTEGER PRIMARY KEY,
    regal TEXT NOT NULL,
    position TEXT NOT NULL,
    led_nummer INTEGER,
    UNIQUE (regal, position)
);
CREATE TABLE IF NOT EXISTS teile (
    id INTEGER PRIMARY KEY,
    bezeichnung TEXT NOT NULL,
    hersteller_nr TEXT NOT NULL DEFAULT '',
    klasse TEXT NOT NULL DEFAULT '',
    menge INTEGER NOT NULL DEFAULT 0 CHECK (menge >= 0),
    eckdaten TEXT NOT NULL DEFAULT '',
    datenblatt_url TEXT NOT NULL DEFAULT '',
    fach_id INTEGER REFERENCES faecher(id),
    angelegt_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alternativen (
    id INTEGER PRIMARY KEY,
    teil_id INTEGER NOT NULL REFERENCES teile(id),
    bezeichnung TEXT NOT NULL,
    hersteller_nr TEXT NOT NULL DEFAULT '',
    hinweis TEXT NOT NULL DEFAULT '',
    datum TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS preis_cache (
    id INTEGER PRIMARY KEY,
    teil_id INTEGER NOT NULL REFERENCES teile(id),
    quelle TEXT NOT NULL,
    preis_eur REAL NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    datum TEXT NOT NULL
);
"""


def verbinde(pfad: Path | str) -> sqlite3.Connection:
    """Öffnet die Bestands-DB und legt fehlende Tabellen an (idempotent)."""
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(pfad)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    return conn
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_db.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add bestand/
git commit -m "E1: Bestands-DB-Schema (teile, faecher, alternativen, preis_cache)"
```

---

### Task 2: Ausgabeformate (`bestand/format.py`)

**Files:**
- Create: `bestand/format.py`
- Test: `bestand/tests/test_format.py`

**Interfaces:**
- Consumes: —
- Produces:
  - `kurzzeile(teil: dict) -> str` — eine Suchtreffer-Zeile; `teil` hat die Schlüssel `id, bezeichnung, menge, klasse, fach` (`fach` ist `"A/3"` oder `None`).
  - `detail(teil: dict, alternativen: list[dict], preise: list[dict]) -> str` — Markdown-Volltext; `alternativen`-Einträge haben `bezeichnung, hersteller_nr, hinweis, datum`; `preise`-Einträge haben `quelle, preis_eur, url, datum`. Jede Preiszeile enthält „Stand vom <datum>".

- [ ] **Step 1: Failing Test schreiben**

```python
"""Ausgabeformate: Kurzzeile fürs Suchergebnis, Markdown-Detail mit Preis-Datum."""
from bestand.format import detail, kurzzeile

TEIL = {"id": 3, "bezeichnung": "100nF X7R 0805", "menge": 250,
        "klasse": "abblock_c", "fach": "A/3", "hersteller_nr": "CL21B104KBCNNNC",
        "eckdaten": "50 V, X7R, 0805", "datenblatt_url": "https://example.com/db.pdf"}


def test_kurzzeile_nennt_id_menge_und_fach():
    zeile = kurzzeile(TEIL)

    assert zeile == "[T-3] 100nF X7R 0805 — Menge 250, Fach A/3, Klasse abblock_c"


def test_kurzzeile_ohne_fach_sagt_das_offen():
    teil = dict(TEIL, fach=None)

    assert "kein Fach zugewiesen" in kurzzeile(teil)


def test_detail_zeigt_preis_nur_mit_stand_vom_datum():
    text = detail(TEIL, alternativen=[], preise=[
        {"quelle": "LCSC", "preis_eur": 0.02, "url": "https://lcsc.com/x",
         "datum": "2026-09-08"}])

    assert "### [T-3] 100nF X7R 0805" in text
    assert "0.02 € bei LCSC — Stand vom 2026-09-08" in text


def test_detail_benennt_leere_abschnitte_statt_sie_wegzulassen():
    text = detail(TEIL, alternativen=[], preise=[])

    assert "Alternativen: keine vermerkt" in text
    assert "Preise: keine im Cache" in text


def test_detail_listet_alternative_mit_datum():
    text = detail(TEIL, alternativen=[
        {"bezeichnung": "GRM21BR71H104KA01", "hersteller_nr": "Murata",
         "hinweis": "gleiches Gehäuse", "datum": "2026-09-08"}], preise=[])

    assert "- GRM21BR71H104KA01 (Murata) — gleiches Gehäuse (vermerkt 2026-09-08)" in text
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_format.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'bestand.format'`

- [ ] **Step 3: Implementierung**

`bestand/format.py`:

```python
"""Ausgabeformate des Bestands: Kurzzeile (Suche) und Markdown-Detail.

Grundsatz aus der Spec (§6): Preise nie ohne Datum ausgeben — jede Preiszeile
trägt „Stand vom <datum>".
"""
from __future__ import annotations


def kurzzeile(teil: dict) -> str:
    fach = f"Fach {teil['fach']}" if teil["fach"] else "kein Fach zugewiesen"
    klasse = teil["klasse"] or "ohne Klasse"
    return (f"[T-{teil['id']}] {teil['bezeichnung']} — Menge {teil['menge']}, "
            f"{fach}, Klasse {klasse}")


def detail(teil: dict, alternativen: list[dict], preise: list[dict]) -> str:
    zeilen = [f"### [T-{teil['id']}] {teil['bezeichnung']}",
              kurzzeile(teil)]
    if teil["hersteller_nr"]:
        zeilen.append(f"Hersteller-Nr: {teil['hersteller_nr']}")
    if teil["eckdaten"]:
        zeilen.append(f"Eckdaten: {teil['eckdaten']}")
    if teil["datenblatt_url"]:
        zeilen.append(f"Datenblatt: {teil['datenblatt_url']}")

    if alternativen:
        zeilen.append("Alternativen:")
        zeilen += [f"- {a['bezeichnung']} ({a['hersteller_nr']}) — "
                   f"{a['hinweis']} (vermerkt {a['datum']})" for a in alternativen]
    else:
        zeilen.append("Alternativen: keine vermerkt")

    if preise:
        zeilen.append("Preise (veralten — Datum beachten):")
        zeilen += [f"- {p['preis_eur']} € bei {p['quelle']} — "
                   f"Stand vom {p['datum']} — {p['url']}" for p in preise]
    else:
        zeilen.append("Preise: keine im Cache")
    return "\n".join(zeilen)
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_format.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add bestand/format.py bestand/tests/test_format.py
git commit -m "E1: Ausgabeformate — Kurzzeile und Detail mit Stand-vom-Datum"
```

---

### Task 3: Dienst — Teil anlegen und suchen (`bestand/service.py`)

**Files:**
- Create: `bestand/service.py`
- Test: `bestand/tests/test_service.py`

**Interfaces:**
- Consumes: `bestand.db.verbinde`, `bestand.format.kurzzeile`, `bestand.format.detail`
- Produces:
  - `class BestandsFehler(Exception)` — fachlicher Fehler, Meldung ist nutzertauglich.
  - `class BestandsDienst` mit `__init__(self, db_pfad, regal_url=None, heute=None, sender=None)` — `heute` ist ein Callable, Default `date.today().isoformat()`; `regal_url`/`sender` werden erst in Task 5 benutzt, stehen aber ab jetzt in der Signatur.
  - `anlegen(bezeichnung, menge, fach, klasse="", hersteller_nr="", eckdaten="", datenblatt_url="") -> str` — `fach` im Format `"Regal/Position"` (z. B. `"A/3"`); unbekanntes Fach wird automatisch angelegt (`led_nummer` bleibt NULL bis E3).
  - `suchen(suchbegriff, klasse=None) -> str` — Teilstring-Suche über Bezeichnung, Hersteller-Nr und Eckdaten; exakte Eingabe `"T-<n>"` liefert stattdessen das Detail (zweistufig wie Wissensschicht F4).

- [ ] **Step 1: Failing Test schreiben**

```python
"""Dienst: Teil anlegen (mit Fach-Auto-Anlage) und zweistufig suchen."""
import pytest

from bestand.service import BestandsDienst, BestandsFehler


@pytest.fixture
def dienst(tmp_path):
    return BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08")


def test_anlegen_meldet_id_menge_und_fach(dienst):
    meldung = dienst.anlegen("100nF X7R 0805", menge=250, fach="A/3",
                             klasse="abblock_c")

    assert meldung == "[T-1] 100nF X7R 0805 angelegt — Menge 250, Fach A/3."


def test_anlegen_legt_unbekanntes_fach_automatisch_an(dienst):
    dienst.anlegen("Teil eins", menge=1, fach="B/7")
    dienst.anlegen("Teil zwei", menge=1, fach="B/7")

    assert "Fach B/7" in dienst.suchen("Teil eins")


def test_anlegen_lehnt_fach_ohne_schraegstrich_ab(dienst):
    with pytest.raises(BestandsFehler, match="Regal/Position"):
        dienst.anlegen("X", menge=1, fach="A3")


def test_suchen_findet_ueber_teilstring_und_liefert_kurzzeilen(dienst):
    dienst.anlegen("100nF X7R 0805", menge=250, fach="A/3", klasse="abblock_c")
    dienst.anlegen("10uF Elko", menge=40, fach="A/4")

    treffer = dienst.suchen("100nF")

    assert "[T-1] 100nF X7R 0805 — Menge 250, Fach A/3" in treffer
    assert "10uF" not in treffer


def test_suchen_filtert_optional_nach_klasse(dienst):
    dienst.anlegen("100nF X7R", menge=1, fach="A/3", klasse="abblock_c")
    dienst.anlegen("100nF Folie", menge=1, fach="A/5", klasse="")

    treffer = dienst.suchen("100nF", klasse="abblock_c")

    assert "X7R" in treffer and "Folie" not in treffer


def test_suchen_mit_t_id_liefert_detail(dienst):
    dienst.anlegen("100nF X7R 0805", menge=250, fach="A/3",
                   hersteller_nr="CL21B104KBCNNNC")

    text = dienst.suchen("T-1")

    assert text.startswith("### [T-1] 100nF X7R 0805")
    assert "Hersteller-Nr: CL21B104KBCNNNC" in text


def test_suchen_ohne_treffer_benennt_das_offen(dienst):
    meldung = dienst.suchen("gibtsnicht")

    assert "Kein Teil gefunden" in meldung
    assert "teil_anlegen" in meldung


def test_unbekannte_t_id_ist_fehler(dienst):
    with pytest.raises(BestandsFehler, match="T-99"):
        dienst.suchen("T-99")
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_service.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'bestand.service'`

- [ ] **Step 3: Implementierung**

`bestand/service.py`:

```python
"""Geschäftslogik des Bestands (Spec §3.2): ein Dienst, eine DB-Datei.

Fehler sind BestandsFehler mit nutzertauglicher Meldung; der MCP-Layer reicht
sie als ⚠-Zeile durch. Datum ist injizierbar (Tests), Default = heute.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from . import db
from . import format as fmt


class BestandsFehler(Exception):
    """Fachlicher Fehler — die Meldung ist für den Nutzer bestimmt."""


class BestandsDienst:
    def __init__(self, db_pfad: Path | str, regal_url: str | None = None,
                 heute=None, sender=None):
        self._conn = db.verbinde(db_pfad)
        self._regal_url = regal_url
        self._heute = heute or (lambda: date.today().isoformat())
        self._sender = sender  # ab Task 5: bestand.regal.sende

    # -- intern ---------------------------------------------------------------

    def _fach_id(self, fach: str) -> int:
        if "/" not in fach:
            raise BestandsFehler(
                f"Fach „{fach}“ nicht verstanden — Format ist Regal/Position, z. B. A/3.")
        regal, position = fach.split("/", 1)
        self._conn.execute(
            "INSERT OR IGNORE INTO faecher (regal, position) VALUES (?, ?)",
            (regal, position))
        zeile = self._conn.execute(
            "SELECT id FROM faecher WHERE regal = ? AND position = ?",
            (regal, position)).fetchone()
        return zeile["id"]

    def _teil(self, teil_id: int) -> dict:
        zeile = self._conn.execute(
            "SELECT t.*, f.regal, f.position FROM teile t"
            " LEFT JOIN faecher f ON f.id = t.fach_id WHERE t.id = ?",
            (teil_id,)).fetchone()
        if zeile is None:
            raise BestandsFehler(f"Kein Teil mit ID T-{teil_id}.")
        d = dict(zeile)
        d["fach"] = f"{d['regal']}/{d['position']}" if d["regal"] else None
        return d

    # -- Werkzeuge ------------------------------------------------------------

    def anlegen(self, bezeichnung: str, menge: int, fach: str, klasse: str = "",
                hersteller_nr: str = "", eckdaten: str = "",
                datenblatt_url: str = "") -> str:
        fach_id = self._fach_id(fach)
        cur = self._conn.execute(
            "INSERT INTO teile (bezeichnung, hersteller_nr, klasse, menge,"
            " eckdaten, datenblatt_url, fach_id, angelegt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (bezeichnung, hersteller_nr, klasse, menge, eckdaten,
             datenblatt_url, fach_id, self._heute()))
        self._conn.commit()
        return (f"[T-{cur.lastrowid}] {bezeichnung} angelegt — "
                f"Menge {menge}, Fach {fach}.")

    def suchen(self, suchbegriff: str, klasse: str | None = None) -> str:
        m = re.fullmatch(r"T-(\d+)", suchbegriff.strip())
        if m:
            teil_id = int(m.group(1))
            alternativen = [dict(z) for z in self._conn.execute(
                "SELECT * FROM alternativen WHERE teil_id = ? ORDER BY datum DESC",
                (teil_id,))]
            preise = [dict(z) for z in self._conn.execute(
                "SELECT * FROM preis_cache WHERE teil_id = ? ORDER BY datum DESC",
                (teil_id,))]
            return fmt.detail(self._teil(teil_id), alternativen, preise)

        muster = f"%{suchbegriff}%"
        sql = ("SELECT t.id, t.bezeichnung, t.menge, t.klasse, f.regal, f.position"
               " FROM teile t LEFT JOIN faecher f ON f.id = t.fach_id"
               " WHERE (t.bezeichnung LIKE ? OR t.hersteller_nr LIKE ?"
               "        OR t.eckdaten LIKE ?)")
        parameter: list = [muster, muster, muster]
        if klasse:
            sql += " AND t.klasse = ?"
            parameter.append(klasse)
        zeilen = self._conn.execute(sql + " ORDER BY t.id", parameter).fetchall()
        if not zeilen:
            return (f"Kein Teil gefunden für „{suchbegriff}“. "
                    "Neu erfassen: teil_anlegen.")
        return "\n".join(fmt.kurzzeile({
            "id": z["id"], "bezeichnung": z["bezeichnung"], "menge": z["menge"],
            "klasse": z["klasse"],
            "fach": f"{z['regal']}/{z['position']}" if z["regal"] else None,
        }) for z in zeilen)
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_service.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add bestand/service.py bestand/tests/test_service.py
git commit -m "E1: Dienst — Teil anlegen mit Fach-Auto-Anlage, zweistufige Suche"
```

---

### Task 4: Dienst — Menge, Alternativen, Preise

**Files:**
- Modify: `bestand/service.py` (Methoden anfügen)
- Test: `bestand/tests/test_service_pflege.py`

**Interfaces:**
- Consumes: `BestandsDienst._teil`, `BestandsFehler`, `self._heute` (Task 3)
- Produces:
  - `menge_aendern(teil_id: int, delta: int) -> str` — relativ (+5 / -2); unter 0 → `BestandsFehler` mit aktuellem Bestand.
  - `alternative_vermerken(teil_id: int, bezeichnung: str, hersteller_nr: str = "", hinweis: str = "") -> str`
  - `preis_cachen(teil_id: int, quelle: str, preis_eur: float, url: str = "") -> str` — `preis_eur <= 0` → `BestandsFehler`; Antwort enthält „Stand vom".

- [ ] **Step 1: Failing Test schreiben**

```python
"""Dienst: Menge relativ ändern, Alternativen und Preise (mit Datum) vermerken."""
import pytest

from bestand.service import BestandsDienst, BestandsFehler


@pytest.fixture
def dienst(tmp_path):
    d = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08")
    d.anlegen("100nF X7R 0805", menge=10, fach="A/3")
    return d


def test_menge_aendern_ist_relativ_und_meldet_neuen_stand(dienst):
    assert dienst.menge_aendern(1, +5) == "[T-1] Menge jetzt 15."
    assert dienst.menge_aendern(1, -12) == "[T-1] Menge jetzt 3."


def test_menge_darf_nicht_unter_null(dienst):
    with pytest.raises(BestandsFehler, match="Bestand: 10"):
        dienst.menge_aendern(1, -11)


def test_menge_aendern_unbekanntes_teil(dienst):
    with pytest.raises(BestandsFehler, match="T-99"):
        dienst.menge_aendern(99, +1)


def test_alternative_erscheint_im_detail(dienst):
    dienst.alternative_vermerken(1, "GRM21BR71H104KA01",
                                 hersteller_nr="Murata", hinweis="gleiches Gehäuse")

    assert "GRM21BR71H104KA01 (Murata) — gleiches Gehäuse (vermerkt 2026-09-08)" \
        in dienst.suchen("T-1")


def test_preis_erscheint_im_detail_mit_stand_vom(dienst):
    meldung = dienst.preis_cachen(1, "LCSC", 0.02, url="https://lcsc.com/x")

    assert "Stand vom 2026-09-08" in meldung
    assert "0.02 € bei LCSC — Stand vom 2026-09-08" in dienst.suchen("T-1")


def test_preis_null_oder_negativ_ist_fehler(dienst):
    with pytest.raises(BestandsFehler, match="Preis"):
        dienst.preis_cachen(1, "LCSC", 0)
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_service_pflege.py -v`
Expected: FAIL mit `AttributeError: ... 'menge_aendern'`

- [ ] **Step 3: Implementierung — Methoden an `BestandsDienst` anfügen**

```python
    def menge_aendern(self, teil_id: int, delta: int) -> str:
        teil = self._teil(teil_id)
        neu = teil["menge"] + delta
        if neu < 0:
            raise BestandsFehler(
                f"[T-{teil_id}] Menge würde unter 0 fallen (Bestand: {teil['menge']}).")
        self._conn.execute("UPDATE teile SET menge = ? WHERE id = ?", (neu, teil_id))
        self._conn.commit()
        return f"[T-{teil_id}] Menge jetzt {neu}."

    def alternative_vermerken(self, teil_id: int, bezeichnung: str,
                              hersteller_nr: str = "", hinweis: str = "") -> str:
        self._teil(teil_id)  # existiert?
        self._conn.execute(
            "INSERT INTO alternativen (teil_id, bezeichnung, hersteller_nr,"
            " hinweis, datum) VALUES (?, ?, ?, ?, ?)",
            (teil_id, bezeichnung, hersteller_nr, hinweis, self._heute()))
        self._conn.commit()
        return f"[T-{teil_id}] Alternative {bezeichnung} vermerkt."

    def preis_cachen(self, teil_id: int, quelle: str, preis_eur: float,
                     url: str = "") -> str:
        if preis_eur <= 0:
            raise BestandsFehler(f"Preis muss > 0 sein, war {preis_eur}.")
        self._teil(teil_id)  # existiert?
        datum = self._heute()
        self._conn.execute(
            "INSERT INTO preis_cache (teil_id, quelle, preis_eur, url, datum)"
            " VALUES (?, ?, ?, ?, ?)", (teil_id, quelle, preis_eur, url, datum))
        self._conn.commit()
        return f"[T-{teil_id}] Preis {preis_eur} € bei {quelle} — Stand vom {datum}."
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_service_pflege.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add bestand/service.py bestand/tests/test_service_pflege.py
git commit -m "E1: Dienst — Menge relativ, Alternativen, Preis-Cache mit Datum"
```

---

### Task 5: Regal-Ansteuerung (`bestand/regal.py` + `fach_leuchten`)

**Files:**
- Create: `bestand/regal.py`
- Modify: `bestand/service.py` (Methode `fach_leuchten` anfügen)
- Test: `bestand/tests/test_regal_leuchten.py`

**Interfaces:**
- Consumes: `BestandsDienst._teil`, `self._regal_url`, `self._sender` (Task 3)
- Produces:
  - `regal.sende(url: str, befehl: dict) -> None` — POST JSON an die Firmware, Timeout 3 s, wirft `OSError` bei Nichterreichbarkeit.
  - `BestandsDienst.fach_leuchten(teil_id: int, farbe: str = "gruen", dauer_s: int = 30) -> str` — ohne `regal_url` nur Fach-Auskunft; bei Sendefehler `BestandsFehler`, der das Fach trotzdem nennt (Spec §6: DB ist die Wahrheit, Regal darf ausfallen). Befehl-Schema (E3-Firmware-Vertrag): `{"led": int | None, "regal": str, "position": str, "farbe": str, "dauer_s": int}`.

- [ ] **Step 1: Failing Test schreiben**

```python
"""fach_leuchten: ohne Regal Auskunft, mit Regal HTTP-Befehl, Ausfall bleibt nützlich."""
import pytest

from bestand.service import BestandsDienst, BestandsFehler


def dienst_mit(tmp_path, **kw):
    d = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08", **kw)
    d.anlegen("100nF X7R 0805", menge=10, fach="A/3")
    return d


def test_ohne_regal_url_kommt_fach_auskunft(tmp_path):
    d = dienst_mit(tmp_path)

    meldung = d.fach_leuchten(1)

    assert meldung == ("Kein Regal konfiguriert (BESTAND_REGAL_URL) — "
                       "[T-1] liegt in Fach A/3.")


def test_mit_regal_url_wird_befehl_gesendet(tmp_path):
    gesendet = {}
    d = dienst_mit(tmp_path, regal_url="http://regal.local/leuchten",
                   sender=lambda url, befehl: gesendet.update(url=url, **befehl))

    meldung = d.fach_leuchten(1, farbe="blau", dauer_s=10)

    assert gesendet == {"url": "http://regal.local/leuchten", "led": None,
                        "regal": "A", "position": "3", "farbe": "blau",
                        "dauer_s": 10}
    assert meldung == "Fach A/3 leuchtet blau (10 s) — [T-1] 100nF X7R 0805."


def test_regal_nicht_erreichbar_nennt_trotzdem_das_fach(tmp_path):
    def kaputt(url, befehl):
        raise OSError("connection refused")
    d = dienst_mit(tmp_path, regal_url="http://regal.local/leuchten", sender=kaputt)

    with pytest.raises(BestandsFehler, match=r"nicht erreichbar.*Fach A/3"):
        d.fach_leuchten(1)


def test_teil_ohne_fach_ist_fehler(tmp_path):
    d = dienst_mit(tmp_path)
    d._conn.execute("UPDATE teile SET fach_id = NULL WHERE id = 1")

    with pytest.raises(BestandsFehler, match="kein Fach"):
        d.fach_leuchten(1)
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_regal_leuchten.py -v`
Expected: FAIL mit `AttributeError: ... 'fach_leuchten'`

- [ ] **Step 3: Implementierung**

`bestand/regal.py`:

```python
"""Leucht-Regal ansteuern: genau ein HTTP-Befehl, mehr kann das Regal nicht (Spec §3.3).

Die Zuordnung Teil→Fach→LED kennt nur die DB; hier wird nur gesendet.
"""
from __future__ import annotations

import json
import urllib.request


def sende(url: str, befehl: dict) -> None:
    """POST an die Regal-Firmware. Wirft OSError, wenn das Regal nicht antwortet."""
    anfrage = urllib.request.Request(
        url, data=json.dumps(befehl).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=3):
        pass
```

An `BestandsDienst` anfügen — und in `__init__` die Zeile `self._sender = sender` ersetzen durch `self._sender = sender or regal.sende` (Import oben ergänzen: `from . import regal`):

```python
    def fach_leuchten(self, teil_id: int, farbe: str = "gruen",
                      dauer_s: int = 30) -> str:
        teil = self._teil(teil_id)
        if teil["fach"] is None:
            raise BestandsFehler(f"[T-{teil_id}] hat kein Fach zugewiesen.")
        if not self._regal_url:
            return (f"Kein Regal konfiguriert (BESTAND_REGAL_URL) — "
                    f"[T-{teil_id}] liegt in Fach {teil['fach']}.")
        fach = self._conn.execute("SELECT * FROM faecher WHERE id = ?",
                                  (teil["fach_id"],)).fetchone()
        befehl = {"led": fach["led_nummer"], "regal": fach["regal"],
                  "position": fach["position"], "farbe": farbe, "dauer_s": dauer_s}
        try:
            self._sender(self._regal_url, befehl)
        except OSError as e:
            raise BestandsFehler(
                f"Regal nicht erreichbar ({e}) — [T-{teil_id}] liegt in "
                f"Fach {teil['fach']}.") from e
        return (f"Fach {teil['fach']} leuchtet {farbe} ({dauer_s} s) — "
                f"[T-{teil_id}] {teil['bezeichnung']}.")
```

- [ ] **Step 4: Alle Tests laufen lassen — müssen bestehen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/ -v`
Expected: 27 passed (4+5+8+6 = 23 aus Tasks 1–4 plus 4 neue; `sender`-Default ändert kein bestehendes Verhalten)

- [ ] **Step 5: Commit**

```bash
git add bestand/regal.py bestand/service.py bestand/tests/test_regal_leuchten.py
git commit -m "E1: fach_leuchten — Fach-Auskunft ohne Regal, HTTP-Befehl mit, Ausfall bleibt nützlich"
```

---

### Task 6: MCP-Server (`bestand/server.py`) + README

**Files:**
- Create: `bestand/server.py`
- Create: `bestand/README.md`
- Create: `bestand/requirements.txt`
- Test: `bestand/tests/test_server.py`

**Interfaces:**
- Consumes: `BestandsDienst` (alle Methoden aus Tasks 3–5), `BestandsFehler`
- Produces: MCP-Server `bestand` mit exakt den sechs Spec-Tools: `teil_suchen`, `teil_anlegen`, `menge_aendern`, `alternative_vermerken`, `preis_cachen`, `fach_leuchten`. `BestandsFehler` wird als `⚠ <meldung>`-String zurückgegeben (kein Tool-Error — die Meldung ist die Antwort). Umgebung: `BESTAND_DB` (Default `~/.hardware-copilot/bestand.db`), `BESTAND_REGAL_URL` (optional).

- [ ] **Step 1: Failing Test schreiben**

```python
"""MCP-Layer: die sechs E1-Tools sind registriert und laufen gegen die DB."""
import asyncio

from bestand import server


def test_alle_sechs_tools_registriert():
    tools = asyncio.run(server.mcp.list_tools())

    namen = {t.name for t in tools}
    assert namen == {"teil_suchen", "teil_anlegen", "menge_aendern",
                     "alternative_vermerken", "preis_cachen", "fach_leuchten"}


def test_anlegen_und_suchen_gegen_konfigurierte_db(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))

    meldung = server.teil_anlegen("100nF X7R 0805", menge=250, fach="A/3")
    assert "[T-1]" in meldung

    assert "Fach A/3" in server.teil_suchen("100nF")


def test_bestandsfehler_wird_als_warnzeile_gemeldet(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))

    meldung = server.teil_suchen("T-99")

    assert meldung.startswith("⚠ ")
    assert "T-99" in meldung
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/test_server.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'bestand.server'`

- [ ] **Step 3: Implementierung**

`bestand/server.py`:

```python
"""MCP-Server des Bestands (Etappe E1): Bestands-DB abfragen und pflegen.

Start:  python -m bestand.server
Konfiguration: BESTAND_DB — Pfad zur SQLite-Datei
(Default: ~/.hardware-copilot/bestand.db); BESTAND_REGAL_URL — optional,
ohne sie meldet fach_leuchten nur das Fach.
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .service import BestandsDienst, BestandsFehler

mcp = MCPServer("bestand")


def _dienst() -> BestandsDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return BestandsDienst(pfad, regal_url=os.environ.get("BESTAND_REGAL_URL"))


def _antwort(aufruf) -> str:
    try:
        return aufruf()
    except BestandsFehler as e:
        return f"⚠ {e}"


@mcp.tool()
def teil_suchen(suchbegriff: str, klasse: str | None = None) -> str:
    """Bestand durchsuchen: Welche Bauteile habe ich da?

    suchbegriff: Teilstring über Bezeichnung, Hersteller-Nummer und Eckdaten
    (z. B. "100nF", "TPS54331"). Exakte Teil-ID "T-3" liefert stattdessen den
    Volltext mit Alternativen und Preisen (Preise immer mit Stand-Datum —
    ältere Preise nie als aktuell ausgeben).
    klasse: optionaler Filter; gleiche Klassen wie im Achsenkatalog des
    Wissens-Repos (SCHEMA.md), z. B. schaltregler, abblock_c, mcu_wifi."""
    return _antwort(lambda: _dienst().suchen(suchbegriff, klasse=klasse))


@mcp.tool()
def teil_anlegen(bezeichnung: str, menge: int, fach: str, klasse: str = "",
                 hersteller_nr: str = "", eckdaten: str = "",
                 datenblatt_url: str = "") -> str:
    """Neues Bauteil im Bestand anlegen.

    fach: Regal/Position, z. B. "A/3" — unbekannte Fächer werden automatisch
    angelegt. klasse: möglichst aus dem Achsenkatalog des Wissens-Repos wählen,
    damit Bestand und Wissensschicht dieselbe Sprache sprechen."""
    return _antwort(lambda: _dienst().anlegen(
        bezeichnung, menge=menge, fach=fach, klasse=klasse,
        hersteller_nr=hersteller_nr, eckdaten=eckdaten,
        datenblatt_url=datenblatt_url))


@mcp.tool()
def menge_aendern(teil_id: int, delta: int) -> str:
    """Bestandsmenge relativ ändern: delta +5 = zugekauft, -2 = verbraucht.
    Unter 0 wird abgelehnt (mit aktuellem Bestand in der Meldung)."""
    return _antwort(lambda: _dienst().menge_aendern(teil_id, delta))


@mcp.tool()
def alternative_vermerken(teil_id: int, bezeichnung: str,
                          hersteller_nr: str = "", hinweis: str = "") -> str:
    """Austausch-Bauteil zu einem Bestandsteil vermerken (z. B. nach Recherche):
    erscheint im Teil-Volltext (teil_suchen mit "T-<id>")."""
    return _antwort(lambda: _dienst().alternative_vermerken(
        teil_id, bezeichnung, hersteller_nr=hersteller_nr, hinweis=hinweis))


@mcp.tool()
def preis_cachen(teil_id: int, quelle: str, preis_eur: float, url: str = "") -> str:
    """Recherchierten Preis zum Teil ablegen. Das Datum setzt der Server;
    Preise werden immer mit „Stand vom <datum>" ausgegeben, weil sie veralten."""
    return _antwort(lambda: _dienst().preis_cachen(
        teil_id, quelle, preis_eur, url=url))


@mcp.tool()
def fach_leuchten(teil_id: int, farbe: str = "gruen", dauer_s: int = 30) -> str:
    """Das Regal-Fach eines Teils aufleuchten lassen (gruen = hier liegt dein
    Teil, blau = hier einsortieren). Ohne konfiguriertes Regal
    (BESTAND_REGAL_URL) wird nur das Fach genannt — auch das beantwortet
    „wo liegt das Teil?"."""
    return _antwort(lambda: _dienst().fach_leuchten(
        teil_id, farbe=farbe, dauer_s=dauer_s))


if __name__ == "__main__":
    mcp.run()
```

`bestand/requirements.txt`:

```
mcp>=2,<3
pytest
```

`bestand/README.md`:

```markdown
# Bestand — MCP-Server (Etappe E1)

Bestands-Datenbank des Hardware-Copilot-Cockpits: Welche Bauteile habe ich,
wo liegen sie, was kosten sie, welche Alternativen sind vermerkt? Entwurf:
`docs/superpowers/specs/2026-09-08-cockpit-bestand-leuchtregal-design.md`.

## Voraussetzungen

- Python ≥ 3.11, MCP-SDK 2.x: `pip install "mcp>=2,<3"` (venv der
  Wissensschicht kann mitbenutzt werden)
- Schreibbarer DB-Pfad — Default `~/.hardware-copilot/bestand.db`

## Einbinden in Claude Code

```bash
claude mcp add bestand -e BESTAND_DB=$HOME/.hardware-copilot/bestand.db \
  -- python -m bestand.server
```

Optional, sobald das Leucht-Regal existiert (Etappe E3):
`-e BESTAND_REGAL_URL=http://<regal-ip>/leuchten`

## Tools (Spec §3.2, E1-Umfang)

| Tool | Zweck |
|---|---|
| `teil_suchen` | Teilstring-Suche (Kurzzeilen); exakte "T-<id>" liefert Volltext mit Alternativen und Preisen (immer mit Stand-Datum). |
| `teil_anlegen` | Teil erfassen; Fach "Regal/Position", unbekannte Fächer werden angelegt. |
| `menge_aendern` | Menge relativ (+zugekauft/−verbraucht); unter 0 abgelehnt. |
| `alternative_vermerken` | Austausch-Bauteil zum Teil notieren. |
| `preis_cachen` | Recherchierten Preis mit Quelle ablegen; Datum setzt der Server. |
| `fach_leuchten` | Regal-Fach aufleuchten lassen; ohne Regal nur Fach-Auskunft. |

## Tests

```bash
python -m pytest bestand/tests/
```

Die Zuordnung Fach→LED (`faecher.led_nummer`) und die Regal-Firmware folgen
in Etappe E3; App-Panels in E2.
```

- [ ] **Step 4: Alle Tests laufen lassen — müssen bestehen**

Run: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest bestand/tests/ wissensschicht/tests/ -v`
Expected: 30 bestand-Tests passed + alle 51 wissensschicht-Tests weiterhin passed

- [ ] **Step 5: Commit**

```bash
git add bestand/
git commit -m "E1: MCP-Server bestand — sechs Tools, README, requirements"
```

---

### Task 7: Gate-Lauf — Einbindung + echte Bestandsfrage im Terminal

Das E1-Gate aus der Spec: *„Welchen 10-µF-Kondensator habe ich?" wird im Terminal korrekt beantwortet; Teile lassen sich anlegen.* Kein neuer Code — Verifikation am eingebundenen Server, Ergebnisse dokumentieren.

**Files:**
- Modify: `bestand/README.md` (Abschnitt „Gate-Lauf E1" mit Datum + Befund anfügen)

- [ ] **Step 1: Server in Claude Code einbinden (user-Scope, wie die Wissensschicht)**

```bash
cd ~/projects/hardware-copilot
claude mcp add bestand \
  -e BESTAND_DB=$HOME/.hardware-copilot/bestand.db \
  -e PYTHONPATH=$HOME/projects/hardware-copilot \
  -- $HOME/projects/hardware-copilot/.venv-wissen/bin/python -m bestand.server
claude mcp list
```

Expected: `bestand ... Connected` (Session ggf. neu starten).

- [ ] **Step 2: Echte Erst-Befüllung über die Tools**

In einer Claude-Code-Session mindestens 5 echte Teile aus real vorhandenem Bestand anlegen lassen (mit echten Fächern), darunter zwei verwechselbare (z. B. zwei verschiedene 10-µF-Kondensatoren). Dann prüfen:

- „Welchen 10-µF-Kondensator habe ich?" → richtige Teile, richtige Fächer, richtige Mengen.
- „Wo liegt T-2?" → `fach_leuchten` antwortet mit Fach-Auskunft (Regal existiert noch nicht).
- „Ich habe 3 davon verbraucht" → `menge_aendern(-3)`, neuer Stand stimmt.
- Preis recherchieren lassen → `preis_cachen`, danach zeigt `teil_suchen("T-…")` den Preis **mit** „Stand vom".
- Absichtlicher Fehlgriff: „T-99 anzeigen" → ⚠-Meldung statt Erfindung.

- [ ] **Step 3: Befund in `bestand/README.md` unter „## Gate-Lauf E1 (Datum)" festhalten**

Drei bis fünf Zeilen: was befüllt, welche Fragen gestellt, Antworten korrekt ja/nein, Auffälligkeiten.

- [ ] **Step 4: Commit**

```bash
git add bestand/README.md
git commit -m "E1: Gate-Lauf dokumentiert — Bestandsfragen im Terminal beantwortet"
```

---

## Self-Review (durchgeführt beim Schreiben)

- **Spec-Abdeckung E1:** Tabellen aus §3.1 (ohne projekte/verbrauch = E5+) ✓ Task 1; sechs Tools aus §3.2 ✓ Tasks 3–6; „Preise nie ohne Datum" (§6) ✓ Tasks 2/4; „Regal darf ausfallen, Meldung bleibt nützlich" (§6) ✓ Task 5; Gate ✓ Task 7; Klassen-Vokabular = Achsenkatalog ✓ als Docstring-Empfehlung (bewusst keine harte Validierung — der Katalog lebt als Markdown im Wissens-Repo; die Wissensschicht meldet unbekannte Klassen ohnehin bei der Abfrage).
- **Platzhalter:** keine — jeder Schritt trägt vollständigen Code bzw. exakte Befehle.
- **Typ-Konsistenz:** `BestandsDienst(db_pfad, regal_url, heute, sender)` ab Task 3 stabil; `fmt.kurzzeile`/`fmt.detail`-Schlüssel (Task 2) identisch mit `_teil`/`suchen` (Task 3); Befehl-Schema in Task 5 = E3-Firmware-Vertrag; Tool-Namen in Task 6 = Spec §3.2 wörtlich.
