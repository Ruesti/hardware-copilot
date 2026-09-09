# E2: App-Cockpit (Bestand-, Teil-Detail- und Wissens-Panel) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Tauri/React-App wird zum Cockpit: Bestand pflegen und Wissen stöbern komplett ohne Terminal (E2-Gate); die alte „App generiert KiCad selbst"-Strecke wird entrümpelt.

**Architecture:** Die Panels reden ausschließlich mit dem FastAPI-Backend (Spec §3.4). Das Backend bekommt zwei neue Router, die dünn auf die vorhandenen Service-Schichten aufsetzen: `bestand.service.BestandsDienst` (bekommt dafür daten-liefernde Methoden neben den MCP-String-Methoden) und `wissensschicht.store/blocks/gaps` (read-only, Dataclasses → JSON). Die alte Claude-API-Strecke (claude_service, Chat/Draft/Validate/Datasheet, Projekt/Spec/Diagram-Welt) fliegt komplett raus — KI läuft per Architektur-Entscheid über Claude Code/Agent SDK (E4), nie über einen API-Key im Backend.

**Tech Stack:** Python ≥ 3.11, FastAPI + Pydantic v2 (camelCase-Alias wie bisher), React 19 + TypeScript + Vite, vitest + @testing-library/react (neu), keine neuen Backend-Abhängigkeiten außer den schon vorhandenen.

## Global Constraints

- Alle Bezeichner, Meldungen, UI-Texte und Tests auf Deutsch; deutsche Typografie („…“, —) in UI-Strings; Preise **nie ohne** „Stand vom <datum>".
- Panels sprechen NUR HTTP mit dem Backend (`src/api/config.ts`, Basis `http://127.0.0.1:8000`) — kein Tauri-invoke, keine KI.
- Backend-Umgebung: `BESTAND_DB` (Default `~/.hardware-copilot/bestand.db`), `WISSENSSCHICHT_REPO` (Default `~/projects/hardware-wissen`) — identisch zu den MCP-Servern; dieselben Dateien sind die eine Wahrheit.
- `bestand/` und `wissensschicht/` bleiben eigenständige Pakete; das Backend importiert ihre Service-/Store-Schicht, niemals umgekehrt. Bestehende MCP-Verhalten (Meldungstexte, Stufen-Regeln) dürfen sich nicht ändern — alle 40 bestand-Tests müssen grün bleiben (91 Python-Tests gesamt mit wissensschicht).
- Wissens-Grundsätze im UI: Stufe immer anzeigen, ⚠ VERMUTUNG-Marker nie unterschlagen.
- Python-Tests: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest <pfad> -v` vom Worktree-Root. Vorher einmalig (Task 2 Step 0): `~/projects/hardware-copilot/.venv-wissen/bin/pip install "fastapi>=0.110" httpx` (Testclient braucht httpx; uvicorn ist fürs Gate nötig: `pip install uvicorn`).
- Frontend: `npm run build` (tsc + vite) muss nach jedem Frontend-Task grün sein; `npx vitest run` für Tests.
- UI-Stil: wie die bestehenden Panels — Inline-Styles, dunkles Theme, Trennlinien `#18181b`, kompakte Typo; kein neues Designsystem, keine CSS-Frameworks.
- Löschungen sind Teil des Auftrags (Spec §3.4/§7): beim Entrümpeln nichts „sicherheitshalber auskommentieren" — löschen; Git bewahrt die Historie.

---

### Task 1: Daten-Methoden im BestandsDienst

**Files:**
- Modify: `bestand/service.py`
- Test: `bestand/tests/test_service_daten.py`

**Interfaces:**
- Consumes: bestehende `BestandsDienst`-Interna (`_conn`, `_teil`, LIKE-Maskierung aus `suchen`)
- Produces (Backend-Router verlässt sich wörtlich darauf):
  - `suche_daten(suchbegriff: str = "", klasse: str | None = None) -> list[dict]` — Schlüssel je Eintrag: `id, bezeichnung, menge, klasse, fach, hersteller_nr` (`fach` = `"A/3"` oder `None`). Leerer Begriff (nach strip) = **alle** Teile (Panel-Liste), sortiert nach id.
  - `teil_daten(teil_id: int) -> dict` — Schlüssel: alle `teile`-Spalten plus `fach`, plus `alternativen: list[dict]` (bezeichnung, hersteller_nr, hinweis, datum; neueste zuerst) und `preise: list[dict]` (quelle, preis_eur, url, datum; neueste zuerst). Wirft `BestandsFehler` bei unbekannter ID.
  - `klassen_daten() -> list[str]` — sortierte distinct nichtleere Klassen aus `teile`.
  - Die MCP-Methode `suchen` nutzt intern dieselbe Logik (kein Verhaltensunterschied: leerer Begriff bleibt dort abgelehnt).

- [ ] **Step 1: Failing Test schreiben**

```python
"""Daten-Methoden für das App-Backend: rohe Dicts statt MCP-Strings."""
import pytest

from bestand.service import BestandsDienst, BestandsFehler


@pytest.fixture
def dienst(tmp_path):
    d = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08")
    d.anlegen("100nF X7R 0805", menge=250, fach="A/3", klasse="abblock_c",
              hersteller_nr="CL21B104KBCNNNC")
    d.anlegen("TPS54331 Buck", menge=4, fach="B/1", klasse="schaltregler")
    return d


def test_suche_daten_leer_liefert_alle(dienst):
    daten = dienst.suche_daten()

    assert [d["id"] for d in daten] == [1, 2]
    assert daten[0]["fach"] == "A/3"
    assert daten[0]["hersteller_nr"] == "CL21B104KBCNNNC"


def test_suche_daten_filtert_begriff_und_klasse(dienst):
    assert [d["id"] for d in dienst.suche_daten("100nF")] == [1]
    assert [d["id"] for d in dienst.suche_daten(klasse="schaltregler")] == [2]
    assert dienst.suche_daten("gibtsnicht") == []


def test_teil_daten_traegt_alternativen_und_preise(dienst):
    dienst.alternative_vermerken(1, "GRM21BR71H104KA01", hersteller_nr="Murata")
    dienst.preis_cachen(1, "LCSC", 0.02, url="https://lcsc.com/x")

    d = dienst.teil_daten(1)

    assert d["bezeichnung"] == "100nF X7R 0805"
    assert d["alternativen"][0]["bezeichnung"] == "GRM21BR71H104KA01"
    assert d["preise"][0] == {"quelle": "LCSC", "preis_eur": 0.02,
                              "url": "https://lcsc.com/x", "datum": "2026-09-08"}


def test_teil_daten_unbekannt_ist_fehler(dienst):
    with pytest.raises(BestandsFehler, match="T-99"):
        dienst.teil_daten(99)


def test_klassen_daten_distinct_sortiert(dienst):
    dienst.anlegen("noch ein C", menge=1, fach="A/4", klasse="abblock_c")

    assert dienst.klassen_daten() == ["abblock_c", "schaltregler"]


def test_mcp_suchen_verhaelt_sich_unveraendert(dienst):
    assert "Suchbegriff ist leer" in dienst.suchen("   ")
    assert "[T-1]" in dienst.suchen("100nF")
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen** (`AttributeError: ... 'suche_daten'`)

- [ ] **Step 3: Implementierung** — in `BestandsDienst` einfügen; `suchen` auf `suche_daten` umstellen:

```python
    def suche_daten(self, suchbegriff: str = "", klasse: str | None = None) -> list[dict]:
        """Rohdaten für das App-Backend: leerer Begriff = alle Teile."""
        suchbegriff = suchbegriff.strip()
        sql = ("SELECT t.id, t.bezeichnung, t.menge, t.klasse, t.hersteller_nr,"
               " f.regal, f.position"
               " FROM teile t LEFT JOIN faecher f ON f.id = t.fach_id")
        klauseln, parameter = [], []
        if suchbegriff:
            maskiert = (suchbegriff.replace("\\", "\\\\")
                        .replace("%", "\\%").replace("_", "\\_"))
            muster = f"%{maskiert}%"
            klauseln.append("(t.bezeichnung LIKE ? ESCAPE '\\'"
                            " OR t.hersteller_nr LIKE ? ESCAPE '\\'"
                            " OR t.eckdaten LIKE ? ESCAPE '\\')")
            parameter += [muster, muster, muster]
        if klasse:
            klauseln.append("t.klasse = ?")
            parameter.append(klasse)
        if klauseln:
            sql += " WHERE " + " AND ".join(klauseln)
        zeilen = self._conn.execute(sql + " ORDER BY t.id", parameter).fetchall()
        return [{"id": z["id"], "bezeichnung": z["bezeichnung"], "menge": z["menge"],
                 "klasse": z["klasse"], "hersteller_nr": z["hersteller_nr"],
                 "fach": f"{z['regal']}/{z['position']}" if z["regal"] else None}
                for z in zeilen]

    def teil_daten(self, teil_id: int) -> dict:
        """Volltext-Rohdaten eines Teils inkl. Alternativen und Preisen."""
        d = self._teil(teil_id)
        d["alternativen"] = [
            {"bezeichnung": z["bezeichnung"], "hersteller_nr": z["hersteller_nr"],
             "hinweis": z["hinweis"], "datum": z["datum"]}
            for z in self._conn.execute(
                "SELECT * FROM alternativen WHERE teil_id = ? ORDER BY datum DESC",
                (teil_id,))]
        d["preise"] = [
            {"quelle": z["quelle"], "preis_eur": z["preis_eur"],
             "url": z["url"], "datum": z["datum"]}
            for z in self._conn.execute(
                "SELECT * FROM preis_cache WHERE teil_id = ? ORDER BY datum DESC",
                (teil_id,))]
        return d

    def klassen_daten(self) -> list[str]:
        """Sortierte, nichtleere Klassen im Bestand (Filter-Dropdown)."""
        return [z["klasse"] for z in self._conn.execute(
            "SELECT DISTINCT klasse FROM teile WHERE klasse != '' ORDER BY klasse")]
```

`suchen` danach so umbauen, dass der Suchpfad `suche_daten` nutzt (T-ID-Zweig nutzt `teil_daten` + bestehendes `fmt.detail`; die Formatierung und alle Meldungen bleiben wörtlich identisch):

```python
    def suchen(self, suchbegriff: str, klasse: str | None = None) -> str:
        suchbegriff = suchbegriff.strip()
        m = re.fullmatch(r"T-(\d+)", suchbegriff)
        if m:
            d = self.teil_daten(int(m.group(1)))
            return fmt.detail(d, d["alternativen"], d["preise"])

        if not suchbegriff:
            return "Suchbegriff ist leer — bitte Begriff oder Teil-ID (T-<n>) angeben."

        daten = self.suche_daten(suchbegriff, klasse=klasse)
        if not daten:
            return (f"Kein Teil gefunden für „{suchbegriff}“. "
                    "Neu erfassen: teil_anlegen.")
        return "\n".join(fmt.kurzzeile(d) for d in daten)
```

(`fmt.detail`/`fmt.kurzzeile` ignorieren überzählige Dict-Schlüssel nicht — sie greifen nur per Key zu, zusätzliche Schlüssel stören nicht.)

- [ ] **Step 4: Alle Bestandstests laufen lassen** — `pytest bestand/tests/ -q`, Expected: **46 passed** (40 + 6 neue; die MCP-Verhaltenstests beweisen die Unveränderlichkeit)

- [ ] **Step 5: Commit** — `E2: Daten-Methoden im BestandsDienst (suche_daten, teil_daten, klassen_daten)`

---

### Task 2: Backend-Router `bestand`

**Files:**
- Create: `backend/__init__.py` (leer, falls fehlt), `backend/app/__init__.py` (leer, falls fehlt), `backend/app/routers/__init__.py` (leer)
- Create: `backend/app/schemas.py`
- Create: `backend/app/routers/bestand.py`
- Test: `backend/tests/__init__.py` (leer), `backend/tests/test_bestand_router.py`

**Interfaces:**
- Consumes: `bestand.service.BestandsDienst` (Task 1: `suche_daten`, `teil_daten`, `klassen_daten`; E1: `anlegen`, `menge_aendern`, `fach_leuchten`), `BestandsFehler`
- Produces (Frontend verlässt sich wörtlich darauf, JSON camelCase):
  - `GET /bestand/teile?suche=&klasse=` → `[{id, bezeichnung, menge, klasse, herstellerNr, fach}]`
  - `GET /bestand/teile/{id}` → `{id, bezeichnung, herstellerNr, klasse, menge, eckdaten, datenblattUrl, fach, alternativen: [{bezeichnung, herstellerNr, hinweis, datum}], preise: [{quelle, preisEur, url, datum}]}` — 404 bei unbekannt
  - `POST /bestand/teile` Body `{bezeichnung, menge, fach, klasse?, herstellerNr?, eckdaten?, datenblattUrl?}` → `{meldung, id}` — 400 mit `detail`=Meldung bei `BestandsFehler`
  - `PATCH /bestand/teile/{id}/menge` Body `{delta}` → `{meldung, menge}` — 400/404
  - `POST /bestand/teile/{id}/leuchten` Body `{farbe?, dauerS?}` → `{meldung}` — 400/404
  - `GET /bestand/klassen` → `["abblock_c", ...]`
  - Modul-Funktion `bestand.routers`-seitig: `_dienst()` liest `BESTAND_DB` pro Request (wie MCP-Server)

- [ ] **Step 0: Test-Abhängigkeiten** — `~/projects/hardware-copilot/.venv-wissen/bin/pip install "fastapi>=0.110" httpx uvicorn` (idempotent)

- [ ] **Step 1: Failing Test schreiben** (`backend/tests/test_bestand_router.py`)

```python
"""Bestand-Router: dünner HTTP-Layer über BestandsDienst, eigene Test-App."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routers.bestand import router
from bestand.service import BestandsDienst


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))
    d = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08")
    d.anlegen("100nF X7R 0805", menge=250, fach="A/3", klasse="abblock_c")
    d.preis_cachen(1, "LCSC", 0.02, url="https://lcsc.com/x")
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_teile_liste_camelcase(client):
    r = client.get("/bestand/teile")

    assert r.status_code == 200
    assert r.json() == [{"id": 1, "bezeichnung": "100nF X7R 0805", "menge": 250,
                         "klasse": "abblock_c", "herstellerNr": "", "fach": "A/3"}]


def test_teile_liste_filtert(client):
    assert client.get("/bestand/teile", params={"suche": "gibtsnicht"}).json() == []
    assert len(client.get("/bestand/teile", params={"klasse": "abblock_c"}).json()) == 1


def test_teil_detail_mit_preisen(client):
    r = client.get("/bestand/teile/1")

    assert r.status_code == 200
    daten = r.json()
    assert daten["datenblattUrl"] == ""
    assert daten["preise"] == [{"quelle": "LCSC", "preisEur": 0.02,
                                "url": "https://lcsc.com/x", "datum": "2026-09-08"}]


def test_teil_detail_unbekannt_404(client):
    r = client.get("/bestand/teile/99")

    assert r.status_code == 404
    assert "T-99" in r.json()["detail"]


def test_teil_anlegen_und_menge(client):
    r = client.post("/bestand/teile", json={"bezeichnung": "10uF Elko",
                                            "menge": 5, "fach": "A/4"})
    assert r.status_code == 200
    assert r.json()["id"] == 2
    assert "angelegt" in r.json()["meldung"]

    r2 = client.patch("/bestand/teile/2/menge", json={"delta": -2})
    assert r2.json()["menge"] == 3

    r3 = client.patch("/bestand/teile/2/menge", json={"delta": -99})
    assert r3.status_code == 400
    assert "unter 0" in r3.json()["detail"]


def test_leuchten_ohne_regal_meldet_fach(client):
    r = client.post("/bestand/teile/1/leuchten", json={})

    assert r.status_code == 200
    assert "Fach A/3" in r.json()["meldung"]


def test_klassen(client):
    assert client.get("/bestand/klassen").json() == ["abblock_c"]
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen** (`ModuleNotFoundError: backend.app.routers`)

- [ ] **Step 3: Implementierung**

`backend/app/schemas.py`:

```python
"""Gemeinsame API-Schemas: camelCase nach außen, snake_case innen (wie bisher)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True,
                              from_attributes=True)
```

`backend/app/routers/bestand.py`:

```python
"""Bestand-Router: dünner HTTP-Layer über bestand.service (Spec §3.4).

Kein eigenes SQL, keine eigene Fachlogik — Meldungen kommen wörtlich aus dem
Dienst, damit App und MCP dieselbe Sprache sprechen.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from bestand.service import BestandsDienst, BestandsFehler

from ..schemas import ApiModel

router = APIRouter(prefix="/bestand", tags=["bestand"])


def _dienst() -> BestandsDienst:
    pfad = os.environ.get("BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db"))
    return BestandsDienst(pfad, regal_url=os.environ.get("BESTAND_REGAL_URL"))


class TeilKurz(ApiModel):
    id: int
    bezeichnung: str
    menge: int
    klasse: str
    hersteller_nr: str
    fach: str | None


class PreisEintrag(ApiModel):
    quelle: str
    preis_eur: float
    url: str
    datum: str


class AlternativeEintrag(ApiModel):
    bezeichnung: str
    hersteller_nr: str
    hinweis: str
    datum: str


class TeilDetail(ApiModel):
    id: int
    bezeichnung: str
    hersteller_nr: str
    klasse: str
    menge: int
    eckdaten: str
    datenblatt_url: str
    fach: str | None
    alternativen: list[AlternativeEintrag]
    preise: list[PreisEintrag]


class TeilNeu(ApiModel):
    bezeichnung: str
    menge: int
    fach: str
    klasse: str = ""
    hersteller_nr: str = ""
    eckdaten: str = ""
    datenblatt_url: str = ""


class MengenDelta(ApiModel):
    delta: int


class LeuchtWunsch(ApiModel):
    farbe: str = "gruen"
    dauer_s: int = 30


@router.get("/teile", response_model=list[TeilKurz], response_model_by_alias=True)
def teile_liste(suche: str = "", klasse: str | None = None):
    return _dienst().suche_daten(suche, klasse=klasse)


@router.get("/teile/{teil_id}", response_model=TeilDetail, response_model_by_alias=True)
def teil_detail(teil_id: int):
    try:
        return _dienst().teil_daten(teil_id)
    except BestandsFehler as e:
        raise HTTPException(404, str(e)) from e


@router.post("/teile")
def teil_anlegen(teil: TeilNeu):
    d = _dienst()
    try:
        meldung = d.anlegen(teil.bezeichnung, menge=teil.menge, fach=teil.fach,
                            klasse=teil.klasse, hersteller_nr=teil.hersteller_nr,
                            eckdaten=teil.eckdaten, datenblatt_url=teil.datenblatt_url)
    except BestandsFehler as e:
        raise HTTPException(400, str(e)) from e
    neu = d.suche_daten()[-1]
    return {"meldung": meldung, "id": neu["id"]}


@router.patch("/teile/{teil_id}/menge")
def menge_aendern(teil_id: int, delta: MengenDelta):
    d = _dienst()
    try:
        meldung = d.menge_aendern(teil_id, delta.delta)
    except BestandsFehler as e:
        raise HTTPException(404 if "Kein Teil" in str(e) else 400, str(e)) from e
    return {"meldung": meldung, "menge": d.teil_daten(teil_id)["menge"]}


@router.post("/teile/{teil_id}/leuchten")
def fach_leuchten(teil_id: int, wunsch: LeuchtWunsch):
    try:
        return {"meldung": _dienst().fach_leuchten(
            teil_id, farbe=wunsch.farbe, dauer_s=wunsch.dauer_s)}
    except BestandsFehler as e:
        raise HTTPException(404 if "Kein Teil" in str(e) else 400, str(e)) from e


@router.get("/klassen")
def klassen():
    return _dienst().klassen_daten()
```

- [ ] **Step 4: Tests laufen lassen** — `pytest backend/tests/ -v`, Expected: 7 passed; danach `pytest bestand/tests/ -q` weiterhin 46 passed

- [ ] **Step 5: Commit** — `E2: Backend-Router bestand (Liste, Detail, Anlegen, Menge, Leuchten, Klassen)`

---

### Task 3: Backend-Router `wissen` (read-only)

**Files:**
- Create: `backend/app/routers/wissen.py`
- Test: `backend/tests/test_wissen_router.py`

**Interfaces:**
- Consumes: `wissensschicht.store.load_rules(repo) -> list[Regel]` (Dataclass mit id, bereich, aussage, begruendung, staerke, stufe, datum_eintrag, datum_geprueft, ausnahmen, quelle: dict, geltung: dict), `wissensschicht.blocks.lade_bloecke(repo) -> list[Block]`, `wissensschicht.blocks.block_volltext(b) -> str`, `wissensschicht.gaps.list_gaps(repo/"luecken.md") -> list[dict]` (datum, frage, grund, status)
- Produces (Frontend verlässt sich wörtlich darauf):
  - `GET /wissen/regeln?klasse=&stufe=` → `[{id, bereich, aussage, staerke, stufe, klasse}]` (klasse = `geltung["klasse"]`)
  - `GET /wissen/regeln/{id}` → volle Regel als Dict (`dataclasses.asdict`) — 404 bei unbekannt
  - `GET /wissen/klassen` → sortierte distinct `geltung.klasse`
  - `GET /wissen/bloecke` → `[{id, titel, kernbauteil, topologie}]`
  - `GET /wissen/bloecke/{id}` → `{**asdict(block), "volltext": block_volltext(block)}` — 404 bei unbekannt
  - `GET /wissen/luecken` → `[{datum, frage, grund, status}]`
  - Fehlerfall Wissens-Repo kaputt (`StoreError`) → 503 mit Meldung (DB ist die Wahrheit; kaputtes Repo klar benennen)

- [ ] **Step 1: Failing Test schreiben** (`backend/tests/test_wissen_router.py`) — Fixture baut ein Mini-Wissens-Repo in `tmp_path`:

```python
"""Wissen-Router: read-only über store/blocks/gaps der Wissensschicht."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routers.wissen import router
from wissensschicht import gaps

REGEL = """\
id = "R-001"
bereich = "schaltregler"
aussage = "Testaussage."
begruendung = "Testbegründung."
staerke = "muss"
stufe = "belegt"
datum_eintrag = 2026-09-08
datum_geprueft = 2026-09-08
ausnahmen = []

[quelle]
typ = "datenblatt"
titel = "Testblatt"
dokument = "DOC1"
fundstelle = "PDF-S. 1"
url = "https://example.com/doc.pdf"
zitat = "Original quote."

[geltung]
klasse = "schaltregler"
"""


@pytest.fixture
def client(tmp_path, monkeypatch):
    d = tmp_path / "regeln" / "schaltregler"
    d.mkdir(parents=True)
    (d / "R-001.toml").write_text(REGEL)
    gaps.report_gap(tmp_path / "luecken.md", "Testfrage", "kein Beleg", "2026-09-08")
    monkeypatch.setenv("WISSENSSCHICHT_REPO", str(tmp_path))
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_regeln_kurzliste(client):
    r = client.get("/wissen/regeln")

    assert r.status_code == 200
    assert r.json() == [{"id": "R-001", "bereich": "schaltregler",
                         "aussage": "Testaussage.", "staerke": "muss",
                         "stufe": "belegt", "klasse": "schaltregler"}]


def test_regeln_filter(client):
    assert client.get("/wissen/regeln", params={"stufe": "vermutung"}).json() == []
    assert len(client.get("/wissen/regeln", params={"klasse": "schaltregler"}).json()) == 1


def test_regel_volltext(client):
    r = client.get("/wissen/regeln/R-001")

    assert r.status_code == 200
    assert r.json()["quelle"]["zitat"] == "Original quote."
    assert client.get("/wissen/regeln/R-999").status_code == 404


def test_klassen(client):
    assert client.get("/wissen/klassen").json() == ["schaltregler"]


def test_luecken(client):
    assert client.get("/wissen/luecken").json() == [
        {"datum": "2026-09-08", "frage": "Testfrage",
         "grund": "kein Beleg", "status": "offen"}]


def test_bloecke_leer(client):
    assert client.get("/wissen/bloecke").json() == []
    assert client.get("/wissen/bloecke/B-001").status_code == 404
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen** (`ModuleNotFoundError: ... wissen`)

- [ ] **Step 3: Implementierung** (`backend/app/routers/wissen.py`):

```python
"""Wissen-Router: read-only Sicht aufs Wissens-Repo (Regeln, Blocks, Lücken).

Dieselben Dateien, die die Wissensschicht der KI serviert — nur als JSON
fürs Panel. Stufen sind Daten; das Frontend zeigt sie unverändert an.
"""
from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException

from wissensschicht.blocks import block_volltext, lade_bloecke
from wissensschicht.gaps import list_gaps
from wissensschicht.store import StoreError, load_rules

router = APIRouter(prefix="/wissen", tags=["wissen"])


def _repo() -> Path:
    return Path(os.environ.get("WISSENSSCHICHT_REPO",
                               str(Path.home() / "projects/hardware-wissen")))


def _regeln():
    try:
        return load_rules(_repo())
    except StoreError as e:
        raise HTTPException(503, f"Wissens-Repo fehlerhaft: {e}") from e


@router.get("/regeln")
def regeln(klasse: str | None = None, stufe: str | None = None):
    ergebnis = []
    for r in _regeln():
        if klasse and r.geltung.get("klasse") != klasse:
            continue
        if stufe and r.stufe != stufe:
            continue
        ergebnis.append({"id": r.id, "bereich": r.bereich, "aussage": r.aussage,
                         "staerke": r.staerke, "stufe": r.stufe,
                         "klasse": r.geltung.get("klasse", "")})
    return ergebnis


@router.get("/regeln/{regel_id}")
def regel(regel_id: str):
    for r in _regeln():
        if r.id == regel_id:
            return asdict(r)
    raise HTTPException(404, f"Keine Regel {regel_id}.")


@router.get("/klassen")
def klassen():
    return sorted({r.geltung.get("klasse", "") for r in _regeln()} - {""})


@router.get("/bloecke")
def bloecke():
    return [{"id": b.id, "titel": b.titel, "kernbauteil": b.kernbauteil,
             "topologie": b.topologie} for b in lade_bloecke(_repo())]


@router.get("/bloecke/{block_id}")
def block(block_id: str):
    for b in lade_bloecke(_repo()):
        if b.id == block_id:
            return {**asdict(b), "volltext": block_volltext(b)}
    raise HTTPException(404, f"Kein Block {block_id}.")


@router.get("/luecken")
def luecken():
    return list_gaps(_repo() / "luecken.md")
```

(Hinweis: Falls die `Block`-Dataclass andere Feldnamen als `titel/kernbauteil/topologie` trägt, VOR dem Implementieren `wissensschicht/blocks.py:29-45` lesen und die Kurzlisten-Felder exakt daran ausrichten — der Test `test_bloecke_leer` bleibt davon unberührt.)

- [ ] **Step 4: Tests laufen lassen** — `pytest backend/tests/ -v`, Expected: 13 passed

- [ ] **Step 5: Commit** — `E2: Backend-Router wissen (Regeln, Blocks, Lücken — read-only)`

---

### Task 4: Backend-Entrümpelung — main.py wird zum Cockpit-Backend

**Files:**
- Rewrite: `backend/app/main.py` (846 → ~40 Zeilen)
- Delete: `backend/app/claude_service.py`, `backend/app/datasheet_fetcher.py`, `backend/app/repository.py`, `backend/app/db.py`, `backend/app/seed.py`, `backend/app/models.py`, `backend/.env.example`
- Modify: `backend/requirements.txt`, `start_backend.sh`
- Test: `backend/tests/test_main_app.py`

**Interfaces:**
- Consumes: Router aus Tasks 2+3
- Produces: `backend.app.main.app` — FastAPI-App mit CORS (localhost:1420/5173 + 127.0.0.1-Varianten), `GET /health` → `{"status": "ok"}`, eingebundenen Routern `/bestand/*` und `/wissen/*` — sonst nichts. Start: `uvicorn backend.app.main:app` vom Repo-Root (damit `bestand`/`wissensschicht` importierbar sind).

- [ ] **Step 1: Failing Test schreiben** (`backend/tests/test_main_app.py`)

```python
"""Die App ist nach der Entrümpelung genau das Cockpit-Backend."""
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_nur_cockpit_routen():
    pfade = {r.path for r in app.routes if hasattr(r, "path")}

    assert any(p.startswith("/bestand") for p in pfade)
    assert any(p.startswith("/wissen") for p in pfade)
    for alt in ("/chat", "/projects", "/draft-circuit", "/validation",
                "/datasheet", "/usage", "/refresh-design"):
        assert not any(p.startswith(alt) for p in pfade), alt
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen** (alte Routen noch da bzw. Import von anthropic scheitert)

- [ ] **Step 3: Implementierung** — neues `backend/app/main.py`:

```python
"""Cockpit-Backend (Spec §3.4): Bestand + Wissen für die App-Panels.

Die alte „App generiert KiCad selbst"-Strecke (Chat/Draft/Validate/Datasheet,
Projekt-Welt, Claude-API) ist entfernt — KiCad läuft über Konnect, KI über
Claude Code (Motor-Schnittstelle folgt in E4). Start vom Repo-Root:
uvicorn backend.app.main:app
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import bestand, wissen

app = FastAPI(title="Hardware-Copilot Cockpit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420",
                   "http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bestand.router)
app.include_router(wissen.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

Dateien löschen (git rm): `claude_service.py`, `datasheet_fetcher.py`, `repository.py`, `db.py`, `seed.py`, `models.py`, `backend/.env.example`. `backend/requirements.txt` neu:

```
fastapi>=0.110
uvicorn[standard]>=0.30
pydantic>=2.7
```

`start_backend.sh`: uvicorn-Zeile ersetzen durch `uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000` (Aufruf vom Repo-Root; `--app-dir backend` entfernen).

- [ ] **Step 4: Tests laufen lassen** — `pytest backend/tests/ bestand/tests/ wissensschicht/tests/ -q`, Expected: **15 + 46 + 51 = 112 passed**

- [ ] **Step 5: Commit** — `E2: Backend entrümpelt — nur noch Cockpit-Routen (bestand, wissen, health)`

---

### Task 5: Frontend-Entrümpelung — App wird zum Cockpit-Rahmen

**Files:**
- Rewrite: `src/App.tsx`, `src/components/layout/AppShell.tsx`
- Delete: `src/components/panels/` (alle 10 alten Panels), `src/components/diagram/` (komplett), `src/components/layout/ProjectSidebar.tsx`, `Sidebar.tsx`, `TopBar.tsx`, `WorkspaceLayout.tsx`, `src/components/ui/Panel.tsx`, `src/api/` (alles außer `config.ts`), `src/types/` (komplett)
- Modify: `package.json` (Dependencies `@xyflow/react`, `n`, `playwright` entfernen)

**Interfaces:**
- Produces: `AppShell` mit zwei Tabs `bestand` („Bestand") und `wissen` („Wissen"), rendert Platzhalter-Divs `<div data-panel="bestand" />` / `<div data-panel="wissen" />`, die Tasks 7/8 durch echte Panels ersetzen. `src/api/config.ts` bleibt unverändert (API_BASE). Dunkles Layout und Kopfleiste im Stil der bisherigen AppShell.

- [ ] **Step 1: Umbau** — `src/App.tsx`:

```tsx
import { useState } from "react";
import { AppShell, type TabId } from "./components/layout/AppShell";

export default function App() {
  const [tab, setTab] = useState<TabId>("bestand");
  return <AppShell tab={tab} onTabChange={setTab} />;
}
```

`src/components/layout/AppShell.tsx` (Stil an der bisherigen Shell orientieren — dunkler Kopf, Tab-Leiste, Inhalt füllt den Rest):

```tsx
export type TabId = "bestand" | "wissen";

const TABS: { id: TabId; label: string }[] = [
  { id: "bestand", label: "Bestand" },
  { id: "wissen", label: "Wissen" },
];

type Props = { tab: TabId; onTabChange: (t: TabId) => void };

export function AppShell({ tab, onTabChange }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh",
                  background: "#09090b", color: "#e4e4e7" }}>
      <header style={{ display: "flex", alignItems: "center", gap: 16,
                       padding: "10px 16px", borderBottom: "1px solid #18181b" }}>
        <strong>Hardware-Copilot</strong>
        <nav style={{ display: "flex", gap: 4 }}>
          {TABS.map((t) => (
            <button key={t.id} onClick={() => onTabChange(t.id)}
              style={{ padding: "6px 14px", borderRadius: 6, border: "none",
                       cursor: "pointer",
                       background: tab === t.id ? "#27272a" : "transparent",
                       color: tab === t.id ? "#fafafa" : "#a1a1aa" }}>
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main style={{ flex: 1, minHeight: 0, display: "flex" }}>
        {tab === "bestand" ? <div data-panel="bestand" /> : <div data-panel="wissen" />}
      </main>
    </div>
  );
}
```

Löschungen per `git rm -r` wie oben gelistet; `package.json`: `@xyflow/react`, `n`, `playwright` aus den Dependencies entfernen, danach `npm install` (Lockfile aktualisiert sich).

- [ ] **Step 2: Build prüfen** — `npm run build`, Expected: grün (tsc findet keine Referenzen auf Gelöschtes mehr — sonst fehlende Löschstelle nachziehen)

- [ ] **Step 3: Commit** — `E2: Frontend entrümpelt — Cockpit-Shell mit Tabs Bestand/Wissen`

---

### Task 6: vitest-Fundament + API-Clients + Typen

**Files:**
- Modify: `package.json` (devDependencies + `"test": "vitest run"`), Create: `vitest.config.ts`
- Create: `src/types/bestand.ts`, `src/types/wissen.ts`
- Create: `src/api/bestand.ts`, `src/api/wissen.ts`
- Test: `src/api/bestand.test.ts`

**Interfaces:**
- Consumes: Backend-Routen aus Tasks 2+3 (camelCase-JSON), `src/api/config.ts` (`API_BASE`)
- Produces (Panels verlassen sich wörtlich darauf):
  - Typen: `TeilKurz {id, bezeichnung, menge, klasse, herstellerNr, fach: string | null}`, `TeilDetail = TeilKurz ohne fach-Einschränkung plus {eckdaten, datenblattUrl, alternativen: AlternativeEintrag[], preise: PreisEintrag[]}`, `AlternativeEintrag {bezeichnung, herstellerNr, hinweis, datum}`, `PreisEintrag {quelle, preisEur, url, datum}`, `TeilNeu {bezeichnung, menge, fach, klasse?, herstellerNr?, eckdaten?, datenblattUrl?}`; `RegelKurz {id, bereich, aussage, staerke, stufe, klasse}`, `RegelVoll` (id, bereich, aussage, begruendung, staerke, stufe, ausnahmen: string[], quelle: Record<string,string>, geltung: Record<string,string>), `BlockKurz {id, titel, kernbauteil, topologie}`, `BlockVoll = BlockKurz & {volltext: string}`, `LueckeEintrag {datum, frage, grund, status}`
  - `api/bestand.ts`: `fetchTeile(suche?, klasse?)`, `fetchTeil(id)`, `createTeil(teil: TeilNeu)`, `patchMenge(id, delta)`, `leuchten(id)`, `fetchBestandKlassen()`
  - `api/wissen.ts`: `fetchRegeln(klasse?, stufe?)`, `fetchRegel(id)`, `fetchWissenKlassen()`, `fetchBloecke()`, `fetchBlock(id)`, `fetchLuecken()`
  - Fehlervertrag: bei `!res.ok` wird `Error(detail aus JSON, sonst Statustext)` geworfen — Panels zeigen `error.message` an.

- [ ] **Step 1: Setup** — `npm install -D vitest @testing-library/react @testing-library/user-event jsdom @testing-library/jest-dom`; `vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", setupFiles: ["./src/test-setup.ts"], globals: true },
});
```

`src/test-setup.ts`: `import "@testing-library/jest-dom/vitest";`
`package.json` scripts: `"test": "vitest run"` ergänzen.

- [ ] **Step 2: Failing Test schreiben** (`src/api/bestand.test.ts`)

```ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { createTeil, fetchTeile } from "./bestand";

const antwort = (daten: unknown, ok = true, status = 200) =>
  Promise.resolve({ ok, status, json: () => Promise.resolve(daten) } as Response);

afterEach(() => vi.unstubAllGlobals());

describe("api/bestand", () => {
  it("fetchTeile hängt Suchparameter an", async () => {
    const f = vi.fn(() => antwort([]));
    vi.stubGlobal("fetch", f);

    await fetchTeile("100nF", "abblock_c");

    const url = String(f.mock.calls[0][0]);
    expect(url).toContain("/bestand/teile?");
    expect(url).toContain("suche=100nF");
    expect(url).toContain("klasse=abblock_c");
  });

  it("wirft die Backend-Meldung als Error", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      antwort({ detail: "Menge muss ≥ 0 sein, war -1." }, false, 400)));

    await expect(createTeil({ bezeichnung: "X", menge: -1, fach: "A/3" }))
      .rejects.toThrow("Menge muss ≥ 0 sein");
  });
});
```

- [ ] **Step 3: Implementierung** — `src/api/bestand.ts` (Muster; `wissen.ts` analog mit seinen sechs Funktionen):

```ts
import { API_BASE } from "./config";
import type { TeilDetail, TeilKurz, TeilNeu } from "../types/bestand";

async function anfrage<T>(pfad: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${pfad}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const daten = await res.json().catch(() => null);
    throw new Error(daten?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export function fetchTeile(suche = "", klasse = ""): Promise<TeilKurz[]> {
  const p = new URLSearchParams();
  if (suche) p.set("suche", suche);
  if (klasse) p.set("klasse", klasse);
  return anfrage(`/bestand/teile?${p}`);
}

export const fetchTeil = (id: number): Promise<TeilDetail> =>
  anfrage(`/bestand/teile/${id}`);

export const createTeil = (teil: TeilNeu): Promise<{ meldung: string; id: number }> =>
  anfrage("/bestand/teile", { method: "POST", body: JSON.stringify(teil) });

export const patchMenge = (id: number, delta: number): Promise<{ meldung: string; menge: number }> =>
  anfrage(`/bestand/teile/${id}/menge`, { method: "PATCH", body: JSON.stringify({ delta }) });

export const leuchten = (id: number): Promise<{ meldung: string }> =>
  anfrage(`/bestand/teile/${id}/leuchten`, { method: "POST", body: JSON.stringify({}) });

export const fetchBestandKlassen = (): Promise<string[]> => anfrage("/bestand/klassen");
```

Typ-Dateien exakt nach dem Interfaces-Block anlegen.

- [ ] **Step 4: Tests + Build** — `npx vitest run` (2 passed), `npm run build` grün

- [ ] **Step 5: Commit** — `E2: vitest-Fundament, API-Clients und Typen für Bestand/Wissen`

---

### Task 7: Bestand-Panel mit Teil-Detail

**Files:**
- Create: `src/components/panels/BestandPanel.tsx`
- Modify: `src/components/layout/AppShell.tsx` (Platzhalter `data-panel="bestand"` ersetzen)
- Test: `src/components/panels/BestandPanel.test.tsx`

**Interfaces:**
- Consumes: `src/api/bestand.ts`, Typen aus `src/types/bestand.ts`
- Produces: `<BestandPanel />` — zweispaltig: links Liste (Suchfeld mit Platzhalter „Suchen — Bezeichnung, Hersteller-Nr, Eckdaten", Klasse-Dropdown „alle Klassen", Button „+ Teil anlegen" öffnet Inline-Formular; je Zeile `[T-3] Bezeichnung`, `Menge · Fach · Klasse`, Buttons „−1"/„+1"); rechts Detail der Auswahl (Stammdaten, Datenblatt als Link, Alternativen-Liste „— keine vermerkt" wenn leer, Preise je Zeile mit `Stand vom <datum>`, Button „Fach leuchten" — Antwort-Meldung erscheint als Statuszeile). Fehler aus der API erscheinen als rote Statuszeile mit `error.message`.

- [ ] **Step 1: Failing Tests schreiben** (`BestandPanel.test.tsx`)

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BestandPanel } from "./BestandPanel";

const TEILE = [{ id: 1, bezeichnung: "100nF X7R 0805", menge: 250,
                 klasse: "abblock_c", herstellerNr: "", fach: "A/3" }];
const DETAIL = { ...TEILE[0], eckdaten: "50 V", datenblattUrl: "",
                 alternativen: [],
                 preise: [{ quelle: "LCSC", preisEur: 0.02, url: "", datum: "2026-09-08" }] };

function mockFetch(routen: Record<string, unknown>) {
  vi.stubGlobal("fetch", vi.fn((eingabe: RequestInfo | URL) => {
    const url = String(eingabe);
    const passend = Object.entries(routen).find(([k]) => url.includes(k));
    return Promise.resolve({ ok: true, status: 200,
      json: () => Promise.resolve(passend ? passend[1] : []) } as Response);
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("BestandPanel", () => {
  it("zeigt Liste und lädt Detail bei Klick", async () => {
    mockFetch({ "/bestand/teile/1": DETAIL, "/bestand/teile": TEILE,
                "/bestand/klassen": ["abblock_c"] });
    render(<BestandPanel />);

    await screen.findByText(/100nF X7R 0805/);
    await userEvent.click(screen.getByText(/100nF X7R 0805/));

    await waitFor(() =>
      expect(screen.getByText(/Stand vom 2026-09-08/)).toBeInTheDocument());
  });

  it("Formular legt Teil an und meldet", async () => {
    mockFetch({ "/bestand/klassen": [], "/bestand/teile": TEILE });
    render(<BestandPanel />);
    await screen.findByText(/100nF/);

    await userEvent.click(screen.getByText("+ Teil anlegen"));
    expect(screen.getByLabelText("Bezeichnung")).toBeInTheDocument();
    expect(screen.getByLabelText("Fach (Regal/Position)")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Tests rot laufen lassen**, dann **Step 3: Implementierung** — `BestandPanel.tsx` als Funktionskomponente (~200 Zeilen), Struktur:

```tsx
import { useCallback, useEffect, useState } from "react";
import { createTeil, fetchBestandKlassen, fetchTeil, fetchTeile,
         leuchten, patchMenge } from "../../api/bestand";
import type { TeilDetail, TeilKurz } from "../../types/bestand";

export function BestandPanel() {
  const [teile, setTeile] = useState<TeilKurz[]>([]);
  const [klassen, setKlassen] = useState<string[]>([]);
  const [suche, setSuche] = useState("");
  const [klasse, setKlasse] = useState("");
  const [auswahl, setAuswahl] = useState<TeilDetail | null>(null);
  const [meldung, setMeldung] = useState("");
  const [fehler, setFehler] = useState("");
  const [formularOffen, setFormularOffen] = useState(false);

  const laden = useCallback(() => {
    fetchTeile(suche, klasse).then(setTeile).catch((e) => setFehler(e.message));
  }, [suche, klasse]);

  useEffect(() => { laden(); }, [laden]);
  useEffect(() => { fetchBestandKlassen().then(setKlassen).catch(() => {}); }, []);

  const detailLaden = (id: number) =>
    fetchTeil(id).then(setAuswahl).catch((e) => setFehler(e.message));

  const mengeAendern = (id: number, delta: number) =>
    patchMenge(id, delta)
      .then((r) => { setMeldung(r.meldung); laden(); if (auswahl?.id === id) detailLaden(id); })
      .catch((e) => setFehler(e.message));
  // … Liste links (Suchfeld, Dropdown, Zeilen mit −1/+1), Formular (Inline,
  // Felder mit <label htmlFor>), Detail rechts (Stammdaten, Alternativen,
  // Preise mit „Stand vom", Knopf „Fach leuchten" → leuchten(id).then(r => setMeldung(r.meldung)))
  // Statuszeile unten: fehler (rot #f87171) vor meldung (grau).
}
```

Vollständige Umsetzung nach dem Interfaces-Block; Formularfelder: Bezeichnung*, Menge* (number, min 0), Fach (Regal/Position)*, Klasse (Dropdown aus `klassen` + Freitext), Hersteller-Nr, Eckdaten, Datenblatt-URL; Absenden → `createTeil` → Meldung anzeigen, Formular zu, `laden()`. AppShell: `<div data-panel="bestand" />` → `<BestandPanel />`.

- [ ] **Step 4: Tests + Build** — `npx vitest run` (alle grün), `npm run build` grün

- [ ] **Step 5: Commit** — `E2: Bestand-Panel mit Teil-Detail (suchen, anlegen, Menge, leuchten)`

---

### Task 8: Wissens-Panel

**Files:**
- Create: `src/components/panels/WissensPanel.tsx`
- Modify: `src/components/layout/AppShell.tsx` (Platzhalter `data-panel="wissen"` ersetzen)
- Test: `src/components/panels/WissensPanel.test.tsx`

**Interfaces:**
- Consumes: `src/api/wissen.ts`, Typen aus `src/types/wissen.ts`
- Produces: `<WissensPanel />` — Sub-Navigation „Regeln | Verified Blocks | Lücken". Regeln: Filter Klasse (Dropdown aus `/wissen/klassen`) + Stufe (alle/belegt/verifiziert/vermutung), Liste `[R-005] aussage` mit Stufen-Badge; Klick → rechts Volltext (Aussage, Begründung, Stärke, Stufe, Quelle mit Fundstelle und Zitat als Blockquote, Geltung, Ausnahmen als Liste). Stufe `vermutung` trägt IMMER den Marker `⚠ VERMUTUNG` (gelb #facc15), `belegt` grün, `verifiziert` blau. Blocks: Liste (id, titel, kernbauteil, topologie), Klick → `volltext` in `<pre>` mit Zeilenumbruch. Lücken: Tabelle Datum/Frage/Grund/Status. Fehler → rote Statuszeile.

- [ ] **Step 1: Failing Tests schreiben** (`WissensPanel.test.tsx`)

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { WissensPanel } from "./WissensPanel";

const REGELN = [
  { id: "R-005", bereich: "schaltregler", aussage: "Hot Loop klein halten.",
    staerke: "muss", stufe: "belegt", klasse: "schaltregler" },
  { id: "R-008", bereich: "schaltregler", aussage: "FB-Massefuß eigener Weg.",
    staerke: "sollte", stufe: "vermutung", klasse: "schaltregler" },
];
const VOLL = { id: "R-008", bereich: "schaltregler", aussage: "FB-Massefuß eigener Weg.",
  begruendung: "Störarme Referenz.", staerke: "sollte", stufe: "vermutung",
  datum_eintrag: "2026-09-08", datum_geprueft: "2026-09-08", ausnahmen: [],
  quelle: { typ: "keine", titel: "", dokument: "", fundstelle: "", url: "", zitat: "" },
  geltung: { klasse: "schaltregler" } };

function mockFetch(routen: Record<string, unknown>) {
  vi.stubGlobal("fetch", vi.fn((eingabe: RequestInfo | URL) => {
    const url = String(eingabe);
    const passend = Object.entries(routen).find(([k]) => url.includes(k));
    return Promise.resolve({ ok: true, status: 200,
      json: () => Promise.resolve(passend ? passend[1] : []) } as Response);
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("WissensPanel", () => {
  it("zeigt Regeln mit Stufen und ⚠-Marker im Volltext", async () => {
    mockFetch({ "/wissen/regeln/R-008": VOLL, "/wissen/regeln": REGELN,
                "/wissen/klassen": ["schaltregler"] });
    render(<WissensPanel />);

    await screen.findByText(/Hot Loop klein halten/);
    await userEvent.click(screen.getByText(/FB-Massefuß eigener Weg/));

    await waitFor(() =>
      expect(screen.getAllByText(/⚠ VERMUTUNG/).length).toBeGreaterThan(0));
  });

  it("wechselt zur Lücken-Tabelle", async () => {
    mockFetch({ "/wissen/luecken": [{ datum: "2026-09-08", frage: "F?",
                                      grund: "kein Beleg", status: "offen" }],
                "/wissen/regeln": [], "/wissen/klassen": [] });
    render(<WissensPanel />);

    await userEvent.click(screen.getByText("Lücken"));

    await screen.findByText("kein Beleg");
  });
});
```

- [ ] **Step 2: rot**, **Step 3: Implementierung** nach dem Interfaces-Block (~220 Zeilen, gleiche Bauart wie BestandPanel: useState für Sub-Tab/Filter/Auswahl, useEffect-Ladelogik, Stufen-Badge als kleine Inline-Komponente `Stufe({stufe})` mit den drei Farben und dem ⚠-Präfix bei vermutung). AppShell-Platzhalter ersetzen.

- [ ] **Step 4: Tests + Build** — `npx vitest run` (alle grün), `npm run build` grün

- [ ] **Step 5: Commit** — `E2: Wissens-Panel (Regeln mit Stufen-Markern, Verified Blocks, Lücken)`

---

### Task 9: Gate-Lauf E2 — Bestand pflegen und Regeln stöbern ohne Terminal

Kein neuer Feature-Code. Ende-zu-Ende am gebauten Frontend gegen das echte Backend, headless per Playwright; Screenshots als Beleg.

**Files:**
- Modify: `bestand/README.md` (Abschnitt „Gate-Lauf E2 (Datum)")
- Modify: `README.md` (Repo-Root: Kurzabschnitt „Cockpit starten" mit den zwei Startbefehlen, alte Phasen-Beschreibung der KiCad-Generator-Pipeline durch 3 Sätze zum Cockpit ersetzen)

- [ ] **Step 1: Stack starten** — Backend mit Gate-DB: `BESTAND_DB=$CLAUDE_JOB_DIR/tmp/gate-e2.db ~/projects/hardware-copilot/.venv-wissen/bin/uvicorn backend.app.main:app --port 8000` (Hintergrund); Frontend: `npm run build && npx vite preview --port 4173` (Hintergrund).
- [ ] **Step 2: Playwright (headless)** — Ablauf: `http://localhost:4173` öffnen → Bestand-Tab: Teil anlegen über das Formular (100nF X7R 0805, Menge 250, Fach A/3, Klasse abblock_c) → erscheint in der Liste → „+1"-Klick erhöht auf 251 → Detail öffnen (leerer Preis-/Alternativen-Zustand sichtbar) → Screenshot 1. Wissens-Tab: Regeln laden (echtes Wissens-Repo, 38 Regeln), Stufe-Filter „vermutung", eine Regel öffnen, ⚠-Marker sichtbar → Screenshot 2; Lücken-Tab → Screenshot 3.
- [ ] **Step 3: Befund dokumentieren** — beide READMEs; Gate-Kriterium aus der Spec wörtlich bewerten: „Bestand pflegen und Regeln stöbern komplett ohne Terminal".
- [ ] **Step 4: Aufräumen** (Prozesse stoppen, Gate-DB liegt im Job-tmp) und **Commit** — `E2: Gate-Lauf dokumentiert — Cockpit pflegt Bestand und zeigt Wissen ohne Terminal`

---

## Self-Review (beim Schreiben durchgeführt)

- **Spec-Abdeckung E2 (§3.4):** Bestand-Panel (suchen/filtern/Menge/anlegen) ✓ T7; Teil-Detail (Eckdaten, Datenblatt, Alternativen, Preis-Historie mit Datum, Fach-leuchten-Knopf) ✓ T7; Wissens-Panel (Regeln nach Klasse+Stufe, Verified Blocks, Lücken, ⚠-Marker) ✓ T8; „Panels reden nur mit Backend" ✓ T2/3/6; Entrümpelung ✓ T4/5; Gate ✓ T9. Alternativen/Preise ERFASSEN in der App bewusst nicht (YAGNI — das macht die KI über MCP; Anzeige genügt laut Spec).
- **Platzhalter:** T7/T8 Step 3 verweisen für die JSX-Vollform auf den Interfaces-Block + Skeleton — bewusster Zuschnitt: Verhalten, Felder, Farben, Zustände und Fehlervertrag sind vollständig spezifiziert, Implementer-Freiheit betrifft nur Markup-Details im vorgegebenen Stil.
- **Typ-Konsistenz:** camelCase-Wire-Format überall (`herstellerNr`, `preisEur`, `datenblattUrl`, `dauerS`); `suche_daten`-Schlüssel (T1) = Router-Modelle (T2) = TS-Typen (T6) = Panel-Nutzung (T7/8) abgeglichen; Testzahlen kumulativ: 46 (bestand) / 13→15 (backend) / 112 gesamt Python.
- **Risiko benannt:** Block-Dataclass-Feldnamen in T3 mit expliziter Verifikationsanweisung.
