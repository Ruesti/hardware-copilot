# E5: Projekte + Stückliste — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Projekte mit vollständiger Stückliste (BOM): KI legt sie per MCP an, der neue Projekt-Tab zeigt je Position Bestandsabgleich (da/knapp/fehlt/nicht zugeordnet), günstigsten Händlerpreis und Fehlteile-Summe; „Als gebaut abbuchen" reduziert den Bestand mit Unterdeckungs-Schutz.

**Architecture:** Neues Modul `bestand/projekte.py` (`ProjektDienst`) auf derselben `bestand.db` — eine Logik, drei Zugänge: 5 neue MCP-Werkzeuge im `bestand`-Server, dünner Router `/projekte`, Projekt-Tab. Abgleich ist reine Ableitung (kein gespeicherter Zustand). Spec: `docs/superpowers/specs/2026-09-10-projekte-kicad-design.md` §2.

**Tech Stack:** wie E1–E4 (Python ≥3.11/sqlite3, FastAPI, MCP-SDK 2.x, React/TS + vitest).

## Global Constraints

- Alles deutsch, deutsche Typografie („…“, —); Preise nie ohne „Stand vom <datum>".
- Statuswerte exakt: `da` / `knapp` / `fehlt` / `nicht_zugeordnet`; Projektstatus `offen` / `gebaut`.
- Preis je Position: **je Quelle der neueste Eintrag, davon der günstigste**; `alle_preise` = neuester Eintrag je Quelle, sortiert nach Preis aufsteigend.
- **Abbuchen lehnt bei Unterdeckung verknüpfter Positionen komplett ab** (mit Benennung der Lücken); nicht zugeordnete Positionen werden übersprungen und im Ergebnis benannt; bereits `gebaut` → Fehler.
- Fehler = `BestandsFehler` (aus `bestand.service` importieren, keine neue Fehlerklasse).
- Bestehende Verhalten unverändert: alle vorhandenen Tests (42 backend + 46 bestand + 51 wissensschicht + 25 vitest) bleiben grün.
- Python-Tests vom Worktree-Root: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest <pfad> -q`; Frontend `npx vitest run` + `npm run build` (Node-20-Pins nicht anfassen).
- Kein `datetime.now()` in Logik — `heute`-Callable wie in `BestandsDienst`.

---

### Task 1: DB-Schema (projekte, projekt_positionen, verbrauch)

**Files:** Modify `bestand/db.py`; Test `bestand/tests/test_db.py` (anfügen)

**Interfaces — Produces:** drei neue Tabellen in `_SCHEMA` (idempotent wie bisher):

```sql
CREATE TABLE IF NOT EXISTS projekte (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    beschreibung TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'offen' CHECK (status IN ('offen', 'gebaut')),
    angelegt_am TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projekt_positionen (
    id INTEGER PRIMARY KEY,
    projekt_id INTEGER NOT NULL REFERENCES projekte(id),
    referenz TEXT NOT NULL,
    bezeichnung TEXT NOT NULL,
    menge INTEGER NOT NULL DEFAULT 1 CHECK (menge > 0),
    klasse TEXT NOT NULL DEFAULT '',
    baugruppe TEXT NOT NULL DEFAULT '',
    teil_id INTEGER REFERENCES teile(id),
    pins TEXT,
    kicad_symbol TEXT NOT NULL DEFAULT '',
    kicad_footprint TEXT NOT NULL DEFAULT '',
    notiz TEXT NOT NULL DEFAULT '',
    UNIQUE (projekt_id, referenz)
);
CREATE TABLE IF NOT EXISTS verbrauch (
    id INTEGER PRIMARY KEY,
    projekt_id INTEGER NOT NULL REFERENCES projekte(id),
    teil_id INTEGER NOT NULL REFERENCES teile(id),
    menge INTEGER NOT NULL,
    datum TEXT NOT NULL
);
```

- [ ] **Step 1: Failing Tests** (an `bestand/tests/test_db.py` anfügen):

```python
def test_verbinde_legt_projekt_tabellen_an(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    tabellen = {z["name"] for z in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"projekte", "projekt_positionen", "verbrauch"} <= tabellen


def test_referenz_ist_je_projekt_eindeutig(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")
    conn.execute("INSERT INTO projekte (name, angelegt_am) VALUES ('P', '2026-09-10')")
    conn.execute("INSERT INTO projekt_positionen (projekt_id, referenz, bezeichnung)"
                 " VALUES (1, 'C3', 'X')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projekt_positionen (projekt_id, referenz, bezeichnung)"
                     " VALUES (1, 'C3', 'Y')")


def test_positions_menge_muss_positiv_sein(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")
    conn.execute("INSERT INTO projekte (name, angelegt_am) VALUES ('P', '2026-09-10')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projekt_positionen (projekt_id, referenz,"
                     " bezeichnung, menge) VALUES (1, 'C3', 'X', 0)")


def test_projekt_status_nur_offen_oder_gebaut(tmp_path):
    conn = verbinde(tmp_path / "bestand.db")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO projekte (name, status, angelegt_am)"
                     " VALUES ('P', 'kaputt', '2026-09-10')")
```

- [ ] **Step 2: rot** → **Step 3:** `_SCHEMA` erweitern (SQL oben, hinter `preis_cache`; Modul-Docstring: „projekte/verbrauch seit E5") → **Step 4:** `pytest bestand/tests/test_db.py -q` alle grün → **Step 5: Commit** `E5: DB-Schema projekte, projekt_positionen, verbrauch`

---

### Task 2: ProjektDienst — anlegen, Positionen, verknüpfen

**Files:** Create `bestand/projekte.py`; Test `bestand/tests/test_projekte.py`

**Interfaces — Produces** (Router/MCP verlassen sich wörtlich darauf):
- `class ProjektDienst:` `__init__(self, db_pfad, heute=None)` (eigene Verbindung via `db.verbinde`; `heute` wie BestandsDienst)
- `anlegen(name: str, beschreibung: str = "") -> str` → `"[P-1] {name} angelegt."`
- `position_hinzufuegen(projekt_id, referenz, bezeichnung, menge=1, klasse="", teil_id=None, baugruppe="", pins=None, kicad_symbol="", kicad_footprint="", notiz="") -> str` — `pins` ist `dict[str, str] | None`, wird als JSON gespeichert. Fehler (`BestandsFehler`): Projekt unbekannt (`"Kein Projekt mit ID P-{id}."`), Projekt `gebaut` („abgeschlossen — keine Änderungen mehr"), Referenz-Duplikat (`"Referenz „{referenz}“ existiert schon in [P-{id}]."`), `menge < 1`, unbekannte `teil_id`. Rückgabe `"[P-1] Position {referenz} ({bezeichnung}) hinzugefügt."`
- `position_verknuepfen(projekt_id, referenz, teil_id) -> str` — Fehler bei unbekanntem Projekt/Referenz/Teil; Rückgabe `"[P-1] {referenz} → [T-{teil_id}] verknüpft."`
- intern `_projekt(projekt_id) -> dict` (Row als dict, Fehler wie oben) — Task 3/4 nutzen es.

- [ ] **Step 1: Failing Tests** (`bestand/tests/test_projekte.py`):

```python
"""ProjektDienst: anlegen, Positionen mit Referenz-Eindeutigkeit, verknüpfen."""
import pytest

from bestand.projekte import ProjektDienst
from bestand.service import BestandsDienst, BestandsFehler


@pytest.fixture
def db_pfad(tmp_path):
    b = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    b.anlegen("100nF X7R 0805", menge=250, fach="A/3", klasse="abblock_c")
    return tmp_path / "bestand.db"


@pytest.fixture
def dienst(db_pfad):
    return ProjektDienst(db_pfad, heute=lambda: "2026-09-10")


def test_anlegen_meldet_id(dienst):
    assert dienst.anlegen("Blink-Board") == "[P-1] Blink-Board angelegt."


def test_position_hinzufuegen_mit_allen_feldern(dienst):
    dienst.anlegen("Blink-Board")

    meldung = dienst.position_hinzufuegen(
        1, "C3", "100nF X7R", menge=2, klasse="abblock_c", teil_id=1,
        baugruppe="Versorgung", pins={"1": "GND", "2": "+3V3"},
        kicad_symbol="Device:C", kicad_footprint="Capacitor_SMD:C_0805")

    assert meldung == "[P-1] Position C3 (100nF X7R) hinzugefügt."


def test_referenz_duplikat_ist_fehler(dienst):
    dienst.anlegen("P")
    dienst.position_hinzufuegen(1, "C3", "X")

    with pytest.raises(BestandsFehler, match="C3"):
        dienst.position_hinzufuegen(1, "C3", "Y")


def test_unbekanntes_projekt_ist_fehler(dienst):
    with pytest.raises(BestandsFehler, match="P-9"):
        dienst.position_hinzufuegen(9, "C1", "X")


def test_unbekanntes_teil_ist_fehler(dienst):
    dienst.anlegen("P")

    with pytest.raises(BestandsFehler, match="T-77"):
        dienst.position_hinzufuegen(1, "C1", "X", teil_id=77)


def test_verknuepfen(dienst):
    dienst.anlegen("P")
    dienst.position_hinzufuegen(1, "C1", "100nF")

    assert dienst.position_verknuepfen(1, "C1", 1) == "[P-1] C1 → [T-1] verknüpft."
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** (`bestand/projekte.py`, Bauart wie `service.py`: Docstring „Projekte + Stückliste (Spec E5 §2)"; `import json`; INSERTs parametrisiert; Duplikat via eigenem SELECT-Check vor INSERT, damit die Meldung deutsch ist statt roher IntegrityError) → **Step 4:** grün → **Step 5: Commit** `E5: ProjektDienst — anlegen, Positionen, verknüpfen`

---

### Task 3: Abgleich + Daten + Text-BOM

**Files:** Modify `bestand/projekte.py`; Test `bestand/tests/test_projekte_abgleich.py`

**Interfaces — Produces:**
- `projekt_daten(projekt_id) -> dict`: `{id, name, beschreibung, status, angelegt_am, positionen: [...], zusammenfassung: {...}}`
  - Position: `{id, referenz, bezeichnung, menge, klasse, baugruppe, teil_id, pins (dict|None), kicad_symbol, kicad_footprint, notiz, bestand: {menge, fach} | None, status, preis: {preis_eur, quelle, datum, url} | None, alle_preise: [wie preis]}` — Status nach Global Constraints; `preis`/`alle_preise` nur bei verknüpftem Teil, sonst `None`/`[]`.
  - `zusammenfassung`: `{positionen: int, gedeckt: int (Status da), fehlen: int (knapp+fehlt+nicht_zugeordnet), fehlteile_kosten_eur: float (Summe fehlmenge×günstigster Preis; fehlmenge = menge−vorrat bei knapp, = menge bei fehlt; ohne Preis nicht eingerechnet), ohne_preis: int (fehlende/knappe Positionen ohne Preisinfo, inkl. nicht_zugeordnet)}`
- `projekte_daten() -> list[{id, name, status, positionen: int, fehlen: int}]` (sortiert nach id)
- `zeigen(projekt_id) -> str` — Text-BOM fürs MCP/Terminal: Kopf `[P-1] Blink-Board — offen · {gedeckt} von {positionen} im Bestand · Fehlteile ≈ {kosten} €`, dann je Baugruppe (leer → `Sonstiges`, alphabetisch) Zeilen `  C3  100nF X7R — 2 benötigt, 250 im Bestand (Fach A/3) — da — 0.02 € bei LCSC (Stand vom 2026-09-10)`; Status-Wörter: `da`, `knapp`, `FEHLT`, `nicht zugeordnet`.

Preis-Ermittlung (Konstante Logik, eigene Hilfsfunktion `_preise_je_teil(teil_id) -> list[dict]`): je Quelle der Eintrag mit höchstem `datum` (bei Gleichstand höchste id), Ergebnis aufsteigend nach `preis_eur`; `preis` = erstes Element.

- [ ] **Step 1: Failing Tests** (`bestand/tests/test_projekte_abgleich.py`):

```python
"""Abgleich: Status, günstigster Händlerpreis, Zusammenfassung, Text-BOM."""
import pytest

from bestand.projekte import ProjektDienst
from bestand.service import BestandsDienst


@pytest.fixture
def aufbau(tmp_path):
    b = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    b.anlegen("100nF X7R 0805", menge=250, fach="A/3", klasse="abblock_c")   # T-1
    b.anlegen("TPS54331", menge=1, fach="B/1", klasse="schaltregler")        # T-2
    b.anlegen("ESP32-S3", menge=0, fach="C/1", klasse="mcu_wifi")            # T-3
    b.preis_cachen(1, "LCSC", 0.02, url="https://l/x")
    b.preis_cachen(1, "Reichelt", 0.05, url="https://r/x")
    b.preis_cachen(3, "Mouser", 4.50, url="https://m/x")
    p = ProjektDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    p.anlegen("Blink-Board")
    p.position_hinzufuegen(1, "C3", "100nF", menge=2, teil_id=1, baugruppe="Versorgung")
    p.position_hinzufuegen(1, "U2", "TPS54331", menge=2, teil_id=2, baugruppe="Versorgung")
    p.position_hinzufuegen(1, "U1", "ESP32-S3", menge=1, teil_id=3, baugruppe="MCU")
    p.position_hinzufuegen(1, "R7", "10k 0603", menge=4)
    return p


def _pos(daten, referenz):
    return next(p for p in daten["positionen"] if p["referenz"] == referenz)


def test_status_ableitung(aufbau):
    daten = aufbau.projekt_daten(1)

    assert _pos(daten, "C3")["status"] == "da"
    assert _pos(daten, "U2")["status"] == "knapp"
    assert _pos(daten, "U1")["status"] == "fehlt"
    assert _pos(daten, "R7")["status"] == "nicht_zugeordnet"


def test_guenstigster_preis_gewinnt(aufbau):
    preis = _pos(aufbau.projekt_daten(1), "C3")["preis"]

    assert preis["quelle"] == "LCSC" and preis["preis_eur"] == 0.02
    assert [p["quelle"] for p in _pos(aufbau.projekt_daten(1), "C3")["alle_preise"]] == \
        ["LCSC", "Reichelt"]


def test_neuester_eintrag_je_quelle(tmp_path):
    b = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-01")
    b.anlegen("X", menge=1, fach="A/1")
    b.preis_cachen(1, "LCSC", 0.10)
    b2 = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    b2.preis_cachen(1, "LCSC", 0.20)
    p = ProjektDienst(tmp_path / "bestand.db")
    p.anlegen("P"); p.position_hinzufuegen(1, "C1", "X", teil_id=1)

    preis = p.projekt_daten(1)["positionen"][0]["preis"]
    assert preis["preis_eur"] == 0.20 and preis["datum"] == "2026-09-10"


def test_zusammenfassung(aufbau):
    z = aufbau.projekt_daten(1)["zusammenfassung"]

    assert z["positionen"] == 4 and z["gedeckt"] == 1 and z["fehlen"] == 3
    # U2 knapp: 1 fehlt, kein Preis → ohne_preis; U1 fehlt: 1×4.50; R7 ohne Preis
    assert z["fehlteile_kosten_eur"] == pytest.approx(4.50)
    assert z["ohne_preis"] == 2


def test_projekte_daten_liste(aufbau):
    liste = aufbau.projekte_daten()

    assert liste == [{"id": 1, "name": "Blink-Board", "status": "offen",
                      "positionen": 4, "fehlen": 3}]


def test_zeigen_gruppiert_und_traegt_stand_vom(aufbau):
    text = aufbau.zeigen(1)

    assert "[P-1] Blink-Board — offen · 1 von 4 im Bestand" in text
    assert text.index("MCU") < text.index("Sonstiges") < text.index("Versorgung")
    assert "Stand vom 2026-09-10" in text
    assert "FEHLT" in text and "nicht zugeordnet" in text
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** → **Step 4:** grün, gesamte bestand-Suite grün → **Step 5: Commit** `E5: Bestandsabgleich, Händlerpreise, Zusammenfassung, Text-BOM`

---

### Task 4: Abbuchen mit Unterdeckungs-Schutz

**Files:** Modify `bestand/projekte.py`; Test `bestand/tests/test_projekte_abbuchen.py`

**Interfaces — Produces:** `abbuchen(projekt_id) -> str` — Regeln: Projekt `gebaut` → Fehler `"[P-1] ist bereits abgebucht."`; Unterdeckung irgendeiner verknüpften Position → `BestandsFehler` mit allen Lücken (`"Nicht genug Bestand: U2 braucht 2, da sind 1; …"`), NICHTS wird gebucht; sonst in EINER Transaktion: je verknüpfter Position `UPDATE teile SET menge = menge - ?` + `INSERT INTO verbrauch`, Projekt-Status → `gebaut`; Rückgabe nennt Anzahl gebuchter Positionen und übersprungene Referenzen (`"[P-1] abgebucht: 3 Positionen. Übersprungen (nicht zugeordnet): R7."`).

- [ ] **Step 1: Failing Tests**:

```python
"""Abbuchen: Unterdeckung lehnt ab, Erfolg bucht + loggt + schließt Projekt."""
import pytest

from bestand.projekte import ProjektDienst
from bestand.service import BestandsDienst, BestandsFehler


@pytest.fixture
def welt(tmp_path):
    b = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    b.anlegen("100nF", menge=10, fach="A/1")   # T-1
    b.anlegen("ESP32", menge=1, fach="B/1")    # T-2
    p = ProjektDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    p.anlegen("P")
    return b, p


def test_unterdeckung_lehnt_komplett_ab(welt):
    b, p = welt
    p.position_hinzufuegen(1, "C1", "100nF", menge=2, teil_id=1)
    p.position_hinzufuegen(1, "U1", "ESP32", menge=3, teil_id=2)

    with pytest.raises(BestandsFehler, match="U1 braucht 3, da sind 1"):
        p.abbuchen(1)
    assert "Menge 10" in b.suchen("T-1")  # nichts gebucht


def test_erfolg_bucht_loggt_und_schliesst(welt):
    b, p = welt
    p.position_hinzufuegen(1, "C1", "100nF", menge=2, teil_id=1)
    p.position_hinzufuegen(1, "R7", "10k", menge=4)  # nicht zugeordnet

    meldung = p.abbuchen(1)

    assert "2 Positionen" not in meldung  # genau 1 verknüpfte gebucht
    assert "1 Position" in meldung and "R7" in meldung
    assert "Menge 8" in b.suchen("T-1")
    assert p.projekt_daten(1)["status"] == "gebaut"
    log = p._conn.execute("SELECT teil_id, menge, datum FROM verbrauch").fetchall()
    assert [(z["teil_id"], z["menge"], z["datum"]) for z in log] == \
        [(1, 2, "2026-09-10")]


def test_doppelt_abbuchen_ist_fehler(welt):
    _, p = welt
    p.position_hinzufuegen(1, "C1", "100nF", menge=1, teil_id=1)
    p.abbuchen(1)

    with pytest.raises(BestandsFehler, match="bereits abgebucht"):
        p.abbuchen(1)
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** (Meldung: bei genau 1 „1 Position", sonst „{n} Positionen"; ohne Übersprungene endet die Meldung nach der Anzahl) → **Step 4:** grün → **Step 5: Commit** `E5: Abbuchen — Unterdeckungs-Schutz, Verbrauchs-Log, Projektabschluss`

---

### Task 5: MCP-Werkzeuge + Motor-Prompt

**Files:** Modify `bestand/server.py`, `backend/app/motor/claude_motor.py` (nur SYSTEM_PROMPT), `bestand/README.md` (Tool-Tabelle ergänzen); Test `bestand/tests/test_server.py` (anfügen)

**Interfaces — Produces:** 5 neue Tools (via `_projekt_dienst()` analog `_dienst()`, Fehler als `⚠`-String via `_antwort`):
`projekt_anlegen(name, beschreibung="")`, `position_hinzufuegen(projekt_id: int, referenz: str, bezeichnung: str, menge: int = 1, klasse: str = "", teil_id: int | None = None, baugruppe: str = "", pins: dict | None = None, kicad_symbol: str = "", kicad_footprint: str = "", notiz: str = "")`, `position_verknuepfen(projekt_id, referenz, teil_id)`, `projekt_zeigen(projekt_id)`, `projekt_abbuchen(projekt_id)`. Docstrings deutsch, mit Hinweisen: Referenzen wie im Schaltplan (C3, U1); `pins` = Pin→Netz fürs spätere KiCad; Klassen aus dem Achsenkatalog.
SYSTEM_PROMPT-Zusatz (wörtlich aus Spec §2.3): *„Beim Schaltungsentwurf lege ein Projekt an (projekt_anlegen) und lege jede gewählte Komponente als Position mit Referenz, Baugruppe und Pin-Netzen ab (position_hinzufuegen); verknüpfe Bestands-Teile (teil_id bzw. position_verknuepfen); liefere kicad_symbol/kicad_footprint mit, wenn bekannt."*

- [ ] **Step 1: Failing Tests** (an `bestand/tests/test_server.py` anfügen):

```python
def test_projekt_tools_registriert():
    tools = asyncio.run(server.mcp.list_tools())

    namen = {t.name for t in tools}
    assert {"projekt_anlegen", "position_hinzufuegen", "position_verknuepfen",
            "projekt_zeigen", "projekt_abbuchen"} <= namen


def test_projekt_rundlauf_ueber_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))
    server.teil_anlegen("100nF", menge=10, fach="A/1")

    assert "[P-1]" in server.projekt_anlegen("Blink-Board")
    server.position_hinzufuegen(1, "C1", "100nF", menge=2, teil_id=1,
                                baugruppe="Versorgung", pins={"1": "GND"})
    text = server.projekt_zeigen(1)
    assert "1 von 1 im Bestand" in text and "Versorgung" in text

    assert "abgebucht" in server.projekt_abbuchen(1)
    assert "Menge 8" in server.teil_suchen("T-1")


def test_projekt_fehler_als_warnzeile(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))

    assert server.projekt_zeigen(9).startswith("⚠ ")
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** (+ SYSTEM_PROMPT-Zusatz; + README-Tabelle) → **Step 4:** `pytest bestand/tests/ backend/tests/ -q` alles grün → **Step 5: Commit** `E5: MCP-Projektwerkzeuge + Motor-Prompt-Zusatz`

---

### Task 6: Router `/projekte`

**Files:** Create `backend/app/routers/projekte.py`; Modify `backend/app/main.py` (include); Test `backend/tests/test_projekte_router.py`

**Interfaces — Produces** (camelCase via `ApiModel` wie `bestand.py`; Frontend verlässt sich wörtlich darauf):
- `GET /projekte` → `[{id, name, status, positionen, fehlen}]`
- `GET /projekte/{id}` → volle `projekt_daten` camelCased: Position mit `teilId, kicadSymbol, kicadFootprint, bestand: {menge, fach}|null, preis: {preisEur, quelle, datum, url}|null, allePreise: [...]`; `zusammenfassung: {positionen, gedeckt, fehlen, fehlteileKostenEur, ohnePreis}`; `pins` bleibt Objekt (`dict[str, str] | null`); `status`-Strings unverändert (`nicht_zugeordnet`). 404 bei unbekannt.
- `POST /projekte` `{name, beschreibung?}` → `{meldung, id}` (id via `projekte_daten()[-1]["id"]`, wie bestand-Muster)
- `POST /projekte/{id}/positionen/{referenz}/zuordnen` `{teilId}` → `{meldung}` — 404/400 nach Meldungsmuster wie `bestand.py`
- `POST /projekte/{id}/abbuchen` → `{meldung}` — 400 bei Unterdeckung/bereits gebaut (Meldung im detail), 404 bei unbekannt
- `_projekt_dienst()` liest `BESTAND_DB` pro Request.

- [ ] **Step 1: Failing Tests** (eigene Test-App wie `test_bestand_router.py`; Fixture legt via Dienste 1 Teil + 1 Projekt mit 2 Positionen an — eine verknüpft/gedeckt, eine nicht zugeordnet):

```python
"""Projekte-Router: Liste, Detail mit Abgleich (camelCase), anlegen, zuordnen, abbuchen."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routers.projekte import router
from bestand.projekte import ProjektDienst
from bestand.service import BestandsDienst


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))
    b = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    b.anlegen("100nF", menge=10, fach="A/1")
    b.preis_cachen(1, "LCSC", 0.02)
    p = ProjektDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-10")
    p.anlegen("Blink-Board")
    p.position_hinzufuegen(1, "C1", "100nF", menge=2, teil_id=1, baugruppe="Versorgung")
    p.position_hinzufuegen(1, "R7", "10k", menge=4)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_liste(client):
    assert client.get("/projekte").json() == [
        {"id": 1, "name": "Blink-Board", "status": "offen",
         "positionen": 2, "fehlen": 1}]


def test_detail_camelcase_mit_abgleich(client):
    daten = client.get("/projekte/1").json()

    c1 = next(p for p in daten["positionen"] if p["referenz"] == "C1")
    assert c1["status"] == "da" and c1["teilId"] == 1
    assert c1["preis"] == {"preisEur": 0.02, "quelle": "LCSC",
                           "datum": "2026-09-10", "url": ""}
    assert daten["zusammenfassung"]["fehlteileKostenEur"] == 0
    assert client.get("/projekte/9").status_code == 404


def test_anlegen_zuordnen_abbuchen(client):
    r = client.post("/projekte", json={"name": "Zweites"})
    assert r.json()["id"] == 2

    r2 = client.post("/projekte/1/positionen/R7/zuordnen", json={"teilId": 1})
    assert "verknüpft" in r2.json()["meldung"]

    r3 = client.post("/projekte/1/abbuchen")
    assert r3.status_code == 200 and "abgebucht" in r3.json()["meldung"]

    r4 = client.post("/projekte/1/abbuchen")
    assert r4.status_code == 400 and "bereits" in r4.json()["detail"]
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** (Pydantic-Modelle `ProjektKurz`, `PositionOut` (+ `BestandOut`, `PreisOut`), `ProjektDetail`, `ZusammenfassungOut`, `ProjektNeu`, `ZuordnenWunsch`; `response_model_by_alias=True`; in `main.py` `include_router(projekte.router)` + `test_nur_cockpit_routen`-Pfadliste um `/projekte` ergänzen falls nötig) → **Step 4:** `pytest backend/tests/ -q` alles grün → **Step 5: Commit** `E5: Router /projekte (Liste, Detail, Anlegen, Zuordnen, Abbuchen)`

---

### Task 7: Frontend API + Typen

**Files:** Create `src/types/projekte.ts`, `src/api/projekte.ts`; Test `src/api/projekte.test.ts`

**Interfaces — Produces:** Typen exakt nach Task-6-Wire-Format (`ProjektKurz`, `PreisEintrag {preisEur, quelle, datum, url}`, `PositionZeile {id, referenz, bezeichnung, menge, klasse, baugruppe, teilId: number|null, pins: Record<string,string>|null, kicadSymbol, kicadFootprint, notiz, bestand: {menge, fach: string|null}|null, status: "da"|"knapp"|"fehlt"|"nicht_zugeordnet", preis: PreisEintrag|null, allePreise: PreisEintrag[]}`, `ProjektDetail`, `Zusammenfassung`). Funktionen über die bestehende `anfrage<T>`-Hilfe: `fetchProjekte()`, `fetchProjekt(id)`, `createProjekt(name, beschreibung?)`, `positionZuordnen(projektId, referenz, teilId)`, `projektAbbuchen(projektId)`. Test wie `bestand.test.ts` (gestubbtes fetch): URL-Formen `/projekte`, `/projekte/1/positionen/C1/zuordnen` (Body `{teilId}`), Fehler-detail wird als Error geworfen.

- [ ] Steps: Test rot → Implementierung → `npx vitest run` grün (+2) → `npm run build` grün → Commit `E5: Projekte-API-Client + Typen`

---

### Task 8: Projekt-Tab + Live-Spiegel

**Files:** Create `src/components/panels/ProjektePanel.tsx`; Modify `src/components/layout/AppShell.tsx` (Tab `projekte` „Projekte", zwischen Bestand und Wissen), `src/components/panels/ChatPanel.tsx` (Live-Spiegel); Test `src/components/panels/ProjektePanel.test.tsx`

**Verhalten (bindend; Stil wie BestandPanel, Inline-Styles dunkel):**
- Links: Projektliste `[P-1] Blink-Board` + Zeile `offen · 4 Positionen · 3 fehlen` (fehlen>0 rot getönt); darunter „+ Projekt anlegen" (Formular Name* + Beschreibung).
- Rechts (Auswahl): Kopf `[P-1] Name — status`, Beschreibung, **Zusammenfassungszeile** `{gedeckt} von {positionen} Positionen im Bestand · Fehlteile ≈ {fehlteileKostenEur} €` (+ ` · {ohnePreis} ohne Preis` falls >0). **BOM-Tabelle gruppiert nach `baugruppe`** (leer → „Sonstiges"; Gruppen alphabetisch, Gruppenkopf gedämpft): Spalten Referenz (monospace), Bezeichnung, benötigt, Bestand (`{menge} · Fach {fach}` oder „—"), Status-Badge (`da` grün #4ade80, `knapp` gelb #facc15, `fehlt` rot #f87171, `nicht zugeordnet` gedämpft gelb), Preis (`{preisEur} € · {quelle} (Stand {datum})`; klickbar → klappt `allePreise`-Liste unter der Zeile auf; ohne Preis „—").
- Zeilen-Aktionen: „Fach leuchten" (nur bei `bestand` mit fach; nutzt `leuchten(teilId)` aus api/bestand); „Zuordnen" (nur bei `teilId === null`): öffnet Auswahl aus `fetchTeile()` → `positionZuordnen` → neu laden.
- Projekt-Aktion „Als gebaut abbuchen" (nur bei status `offen`; `window.confirm`; Erfolg/Fehler-Meldung als Statuszeile unten, danach neu laden — Fehlermeldung des Backends wörtlich).
- **Live-Spiegel:** ChatPanel feuert zusätzlich `projekt-geaendert`, wenn `werkzeug_fertig.name` `"projekt"` ODER `"position"` enthält (zusätzlich zum bestehenden bestand-Event — `projekt_abbuchen` ändert auch Bestand, das bestehende `mcp__bestand`-Event deckt das ab). ProjektePanel-Listener auf `projekt-geaendert` → Liste + Detail neu laden.
- Tests (Mock-fetch wie BestandPanel-Tests): (1) Liste rendert, Klick lädt Detail mit Statusbadges und Zusammenfassung; (2) „nicht zugeordnet"-Zeile zeigt Zuordnen, `da`-Zeile nicht; (3) ChatPanel: `werkzeug_fertig` mit name `mcp__bestand__position_hinzufuegen` dispatcht `projekt-geaendert` (Spy).

- [ ] Steps: Tests rot → Implementierung (~260 Zeilen) → `npx vitest run` alle grün → `npm run build` grün → Commit `E5: Projekt-Tab mit BOM-Tabelle, Zuordnen, Abbuchen, Live-Spiegel`

---

### Task 9: Gate-Lauf E5 (Controller)

Kein neuer Code. Ablauf wie E4-Gate (headless Chromium, Backend mit Gate-DB, echte Claude-Session):
1. Gate-DB mit 2–3 Teilen + Preisen befüllen; Stack starten (uvicorn + vite preview).
2. Chat-Anfrage: „Lege ein Projekt ‚Blink-Board' an: U1 ESP32-S3 (Baugruppe MCU), C1+C2 100nF Entkopplung (Baugruppe Versorgung, verknüpfe mit passenden Bestands-Teilen), R1 10k (nicht im Bestand). Nutze die Projektwerkzeuge, Pin-Netze wo sinnvoll."
3. Prüfen: Projekt-Tab zeigt BOM gruppiert, Status gemischt, Fehlteile-Summe; Abbuchen über die UI: erst Unterdeckungs-Fall (falls konstruierbar) bzw. Erfolg → Bestand-Tab zeigt reduzierte Mengen. Screenshots.
4. Befund in `bestand/README.md` („Gate-Lauf E5"), Commit `E5: Gate-Lauf dokumentiert`.
Danach: Whole-Branch-Review (stärkstes Modell), Fixes, Push auf PR #9.

---

## Self-Review (beim Schreiben)

- **Spec-Abdeckung §2:** 2.1 Datenmodell ✓ T1; 2.2 Abgleich+Preise+Kopfzeile ✓ T3; 2.3 MCP+Prompt ✓ T5; 2.4 Tab+Router+Live-Spiegel ✓ T6–T8; 2.5 Fehlerverhalten ✓ T2 (Duplikat), T4 (Unterdeckung/Übersprungene/doppelt). §5-Gate ✓ T9.
- **Platzhalter:** T8-JSX bewusst als bindende Verhaltensspez. (Muster BestandPanel), sonst Vollcode.
- **Typ-Konsistenz:** Statuswerte, Preis-Schlüssel (`preis_eur`↔`preisEur`), Zusammenfassungs-Felder in T3=T6=T7=T8 abgeglichen; `pins` überall `dict|None` bzw. `Record|null`.
- **Testzahlen:** bewusst keine harten Gesamtsummen (Lektion aus E2) — Kriterium ist „alle grün, keine Regressionen" plus die neuen Testdateien.
