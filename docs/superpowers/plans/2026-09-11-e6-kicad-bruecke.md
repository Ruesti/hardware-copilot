# E6: KiCad-Brücke — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus einem E5-Projekt entstehen per Knopfdruck drei Artefakte: `.kicad_sch` mit Netz-Label-Stummeln, ungeroutete `.kicad_pcb` mit Baugruppen-Platzierung und eine Routing-Anleitung, die ausschließlich aus der Wissensbasis gespeist wird (Spec §3).

**Architecture:** Die sauberen Bausteine vom nie gemergten Branch `feat/kicad-export` (S-Expression-Writer, Symbol-Extraktion, Bauteil-Bibliothek, Footprint-Raten, PCB-Erzeugung, pcbnew-Check) werden nach `backend/app/kicad/` portiert — Import-Anpassung, keine Neuerfindung. Neu sind nur: `modell.py` (die zwei Dataclasses + Bauer aus Projekt-Positionen statt der alten Blocks/Components-Welt), `anleitung.py` (Wissensbasis-Guide, ersetzt die hartkodierte guide.py ersatzlos) und der schlanke Orchestrator + Router-Endpunkte + Export-UI im Projekt-Tab. KiCad 9.0.2 ist auf dem NUC komplett installiert (kicad-cli, pcbnew, /usr/share/kicad/symbols) — Tests nutzen echtes ERC als Wahrheitsinstanz; auf Maschinen ohne KiCad greifen `requires_kicad`-Skips.

**Tech Stack:** wie bisher + `pyyaml` (Bauteil-Bibliothek parts.yaml).

## Global Constraints

- Alles deutsch, deutsche Typografie; kein `datetime.now()` in Logik — `heute`-Callable durchreichen.
- Portierte Dateien möglichst UNVERÄNDERT übernehmen (nur Imports anpassen: `from app.…` → relative bzw. `.modell` statt `.netlist`); keine stilistischen Umbauten — Reviewbarkeit der Portierung geht vor.
- Kein Auto-Routing (Spec §6). PCB nur Platzierung + Netz-Pads.
- Symbol-Zuordnung dreistufig (Spec §3.1): explizites `kicad_symbol` der Position → Bibliothek per Hersteller-Nr → **Mapping-Report** („übersprungen"), nie stilles Fehlen.
- Anleitung: einzige Quelle Wissensbasis (`WISSENSSCHICHT_REPO`); Stufen/Quellen/Zitate anzeigen, ⚠ VERMUTUNG nie unterschlagen; Heikel-Warnblock.
- Ausgabe: `$HARDWARE_COPILOT_EXPORTE` (Default `~/hardware-copilot-exporte`) `/<slug>/`.
- Python-Tests vom Worktree-Root: `~/projects/hardware-copilot/.venv-wissen/bin/python -m pytest <pfad> -q`; einmalig `~/projects/hardware-copilot/.venv-wissen/bin/pip install pyyaml` (Task 1 Step 0) + `pyyaml` in `backend/requirements.txt`.
- Frontend: `npx vitest run` + `npm run build` grün; Node-20-Pins nicht anfassen.
- Bestehende Suiten (115 backend+bestand, 51 wissensschicht, 30 vitest) bleiben grün.

---

### Task 1: Portierung der Basismodule + ERC-Testinfrastruktur

**Files:**
- Create (per `git show feat/kicad-export:<pfad> > <ziel>`, dann Imports anpassen):
  - `backend/app/kicad/__init__.py` (leer, neu)
  - `backend/app/kicad/sexpr.py` ← `backend/app/kicad/sexpr.py`
  - `backend/app/kicad/symbols.py` ← dito
  - `backend/app/kicad/library.py` ← dito (LIBRARY_PATH zeigt auf `backend/library/parts.yaml` — Pfadberechnung prüfen: `Path(__file__).resolve().parent.parent.parent / "library" / "parts.yaml"` ergibt vom neuen Ort `backend/library/parts.yaml` — stimmt)
  - `backend/library/parts.yaml` ← `backend/library/parts.yaml`
  - `backend/app/kicad/footprints.py` ← dito
  - `backend/app/kicad/sch_writer.py` ← dito, Import `from .netlist import …` → `from .modell import ExportModel, SymbolInstance`
  - `backend/app/kicad/modell.py` — NEU: exakt die Dataclasses `SymbolInstance` und `ExportModel` aus `feat/kicad-export:backend/app/kicad/netlist.py` (Felder: ref, lib_id, value, footprint, block_name, pin_nets, status, name="", component_id="", net_role=None bzw. instances/unmapped/warnings) — wörtlich kopieren, Modul-Docstring: „Export-Modell (E6): Dataclasses aus dem alten netlist.py; der Bauer aus Projekt-Positionen folgt in Task 2."
- Test: `backend/tests/kicad_conftest.py` ← alte `backend/tests/conftest.py`-Inhalte (KICAD_SYMBOLS, HAS_KICAD_CLI, requires_kicad, run_erc) als importierbares Modul (NICHT conftest.py nennen — es gibt schon Testdateien; Import in Tests via `from .kicad_conftest import …` bzw. `from backend.tests.kicad_conftest import …`); `backend/tests/test_kicad_sch_writer.py` ← alte `test_sch_writer.py`, Imports auf `backend.app.kicad.modell`/`sch_writer` und `kicad_conftest` umgestellt, sonst unverändert.

**Interfaces — Produces:** `modell.ExportModel`/`SymbolInstance` (Feldnamen wie oben); `sch_writer.write_schematic(model, symbols_dir: Path, project_name: str) -> str`; `library.load_library() -> Library` mit `for_component(mpn, comp_type) -> LibraryPart | None` (`LibraryPart.lib_id/footprint/role_to_pin/validated`); `footprints.guess_footprint(comp_type, package, mount="smd") -> str`; `kicad_conftest.requires_kicad`, `run_erc(sch_path) -> (fehler, text)`.

- [ ] **Step 0:** `~/projects/hardware-copilot/.venv-wissen/bin/pip install pyyaml`; `pyyaml` in `backend/requirements.txt` ergänzen.
- [ ] **Step 1:** Dateien portieren (git show-Redirects), Imports minimal anpassen. `git show feat/kicad-export:backend/tests/fixtures/minimal.kicad_sch > backend/tests/fixtures/minimal.kicad_sch` falls von Tests gebraucht (prüfen).
- [ ] **Step 2:** `pytest backend/tests/test_kicad_sch_writer.py -q` — die portierten Tests (inkl. ERC-Läufe, KiCad ist auf dem NUC da) müssen grün laufen. Scheitert ein Test an echten Portierungslücken (fehlendes Modul), fehlende Datei nachportieren; INHALTLICHE Testanpassungen nur, wo alte Datenmodell-Reste (app.repository o. ä.) referenziert werden — im Report dokumentieren.
- [ ] **Step 3:** Alle Suiten grün (`pytest backend/tests/ bestand/tests/ -q`).
- [ ] **Step 4: Commit** `E6: KiCad-Bausteine portiert (sexpr, symbols, library, footprints, sch_writer) + ERC-Testinfra`

---

### Task 2: Modell-Bauer aus Projekt-Positionen

**Files:** Modify `backend/app/kicad/modell.py`, `bestand/projekte.py` (eine Zeile: `bestand`-Dict um `hersteller_nr` ergänzen); Test `backend/tests/test_kicad_modell.py`

**Interfaces:**
- Consumes: `projekt_daten`-Dict (E5; Positionen mit referenz/bezeichnung/menge/klasse/baugruppe/pins/kicad_symbol/kicad_footprint/bestand), `library.Library`
- Produces: `baue_export_modell(projekt: dict, library: Library) -> ExportModel`
  - je Position eine `SymbolInstance`: `ref=referenz`, `value=bezeichnung`, `block_name=baugruppe or "Sonstiges"`, `pin_nets=pins or {}`, `name=bezeichnung`
  - lib_id-Kaskade: `kicad_symbol` gesetzt → nutzen, `status="mapped"`; sonst Bibliothek per `for_component(hersteller_nr_des_verknuepften_teils, None)` → `part.lib_id`, `status="mapped"`; sonst Position in `unmapped` (`{"referenz", "bezeichnung", "grund": "kein KiCad-Symbol — kicad_symbol angeben oder Teil in parts.yaml aufnehmen"}`) und KEINE Instanz
  - footprint-Kaskade: `kicad_footprint` gesetzt → nutzen; sonst `part.footprint` (falls Bibliothekstreffer); sonst `""`
  - `menge > 1` → Warnung `"{referenz}: Menge {n} — im Schaltplan ein Symbol je Referenz; für mehrere Exemplare eigene Referenzen anlegen."`
  - Position ohne pins → Warnung `"{referenz}: keine Pin-Netze — Symbol wird unverdrahtet platziert."`
- Dafür in `bestand/projekte.py` `_position_daten`: `bestand`-Dict zusätzlich mit `"hersteller_nr": teil["hersteller_nr"]` (additiv; Router-Pydantic ignoriert Extra-Keys — bestehende Tests bleiben grün).

- [ ] **Step 1: Failing Tests** (`backend/tests/test_kicad_modell.py`):

```python
"""Modell-Bauer: Projekt-Positionen → ExportModel (Kaskade, Report, Warnungen)."""
from backend.app.kicad.library import Library, LibraryPart
from backend.app.kicad.modell import baue_export_modell


def projekt(positionen):
    return {"id": 1, "name": "Blink-Board", "status": "offen", "positionen": positionen}


def pos(**kw):
    basis = {"referenz": "C1", "bezeichnung": "100nF", "menge": 1, "klasse": "",
             "baugruppe": "", "pins": None, "kicad_symbol": "", "kicad_footprint": "",
             "notiz": "", "teil_id": None, "bestand": None, "preis": None,
             "alle_preise": [], "id": 1}
    basis.update(kw)
    return basis


LEER = Library()
MIT_MCP = Library(parts={"MCP73831T-2ACI/OT": LibraryPart(
    lib_id="Battery_Management:MCP73831-2-OT",
    footprint="Package_TO_SOT_SMD:SOT-23-5", role_to_pin={})})


def test_explizites_symbol_gewinnt():
    m = baue_export_modell(projekt([pos(kicad_symbol="Device:C",
                                        pins={"1": "GND", "2": "+3V3"},
                                        baugruppe="Versorgung")]), LEER)

    inst = m.instances[0]
    assert inst.lib_id == "Device:C" and inst.status == "mapped"
    assert inst.block_name == "Versorgung"
    assert inst.pin_nets == {"1": "GND", "2": "+3V3"}
    assert m.unmapped == []


def test_bibliothek_per_herstellernummer():
    p = pos(referenz="U1", bezeichnung="MCP73831",
            bestand={"menge": 3, "fach": "B/1", "hersteller_nr": "MCP73831T-2ACI/OT"})

    m = baue_export_modell(projekt([p]), MIT_MCP)

    assert m.instances[0].lib_id == "Battery_Management:MCP73831-2-OT"
    assert m.instances[0].footprint == "Package_TO_SOT_SMD:SOT-23-5"


def test_ohne_zuordnung_landet_im_report():
    m = baue_export_modell(projekt([pos(referenz="R7", bezeichnung="10k")]), LEER)

    assert m.instances == []
    assert m.unmapped[0]["referenz"] == "R7"
    assert "kicad_symbol" in m.unmapped[0]["grund"]


def test_warnungen_menge_und_pins():
    m = baue_export_modell(projekt([
        pos(referenz="C1", kicad_symbol="Device:C", menge=2),
    ]), LEER)

    assert any("Menge 2" in w for w in m.warnings)
    assert any("keine Pin-Netze" in w for w in m.warnings)


def test_leere_baugruppe_wird_sonstiges():
    m = baue_export_modell(projekt([pos(kicad_symbol="Device:C")]), LEER)

    assert m.instances[0].block_name == "Sonstiges"
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** (+ `hersteller_nr` in `_position_daten`; kleiner Test dafür an `bestand/tests/test_projekte_abgleich.py` anfügen: `assert _pos(daten, "C3")["bestand"]["hersteller_nr"] == ""` bzw. mit gesetzter Nummer) → **Step 4:** alle Suiten grün → **Step 5: Commit** `E6: Modell-Bauer aus Projekt-Positionen (Kaskade, Mapping-Report, Warnungen)`

---

### Task 3: PCB-Portierung (Baugruppen-Platzierung, ungeroutet)

**Files:** Create (Port wie Task 1): `backend/app/kicad/pcb.py` (Import `.netlist` → `.modell`), `backend/app/kicad/pcb_build_script.py`, `backend/app/kicad/system.py`; Test `backend/tests/test_kicad_pcb.py` ← alte `test_pcb.py` (Imports angepasst; `requires_kicad`-artige Skips → pcbnew-Skip via `pcb.pcbnew_available()`).

**Interfaces — Produces:** `pcb.build_pcb(model: ExportModel, out_path: Path) -> list[dict]` (übersprungene ohne Footprint), `pcb.pcbnew_available() -> bool`, `system.kicad_status() -> dict`.

- [ ] Steps: portieren → alte Tests grün (auf NUC läuft pcbnew real) → alle Suiten grün → Commit `E6: PCB-Erzeugung portiert — Baugruppen-Spalten, Netz-Pads, ungeroutet`

---

### Task 4: Routing-Anleitung aus der Wissensbasis

**Files:** Create `backend/app/kicad/anleitung.py`; Test `backend/tests/test_kicad_anleitung.py`

**Interfaces:**
- Consumes: `projekt_daten`-Dict, `wissensschicht.store.load_rules`, `heikel.toml` im Wissens-Repo (Struktur vor Implementierung in `wissensschicht/heikel.py` nachlesen und dessen Loader wiederverwenden, falls exportiert — sonst `tomllib` direkt)
- Produces:
  - `projekt_hinweise(projekt: dict, wissens_repo: Path) -> dict` mit `{"hinweise": [{"regel_id", "stufe", "staerke", "aussage", "begruendung", "quelle": str, "zitat": str, "referenzen": [str]}], "heikel": [{"bereich", "hinweis"}], "ohne_regeln": [klassen ohne Treffer]}` — Regeln gefiltert auf `geltung.klasse` ∈ Klassen der Positionen; `referenzen` = Referenzen der Positionen dieser Klasse (sortiert); Heikel-Eintrag, wenn ein Heikel-Bereich eine der BOM-Klassen führt.
  - `baue_anleitung(projekt: dict, wissens_repo: Path, heute: str) -> str` — dunkles HTML (Inline-CSS): Titel „Routing-Anleitung — {name} (Stand {heute})", Heikel-Warnblock oben (gelber Rahmen), dann je Regel eine Karte: Badge (BELEGT grün / ⚠ VERMUTUNG gelb / VERIFIZIERT blau) + Stärke, Aussage fett, „betrifft: C1, C2", Begründung, Quelle-Zeile, Zitat als `<blockquote>`. `html.escape` für ALLE Repo-Texte. Fußzeile: „Einzige Quelle: Wissensbasis {repo} — Stufen sind Daten, nie hochgestuft."

- [ ] **Step 1: Failing Tests** (tmp-Wissensrepo mit dem REGEL-Template aus `backend/tests/test_wissen_router.py` — eine belegte schaltregler-Regel R-001, eine Vermutungs-Regel R-002 für abblock_c (quelle typ „keine"), eine mcu_wifi-Regel R-003, plus `heikel.toml` mit einem Bereich, der `klassen = ["schaltregler"]` führt — exakte heikel.toml-Feldnamen beim Implementieren aus `wissensschicht/heikel.py`/echtem Repo übernehmen):

```python
def test_hinweise_filtern_nach_bom_klassen(wissens_repo):
    projekt = {"name": "P", "positionen": [
        {"referenz": "U2", "klasse": "schaltregler"},
        {"referenz": "C1", "klasse": "abblock_c"},
        {"referenz": "C2", "klasse": "abblock_c"},
    ]}

    h = projekt_hinweise(projekt, wissens_repo)

    ids = {x["regel_id"] for x in h["hinweise"]}
    assert ids == {"R-001", "R-002"}          # R-003 (mcu_wifi) nicht in der BOM
    abblock = next(x for x in h["hinweise"] if x["regel_id"] == "R-002")
    assert abblock["referenzen"] == ["C1", "C2"]
    assert abblock["stufe"] == "vermutung"


def test_heikel_warnung_bei_betroffener_klasse(wissens_repo):
    projekt = {"name": "P", "positionen": [{"referenz": "U2", "klasse": "schaltregler"}]}

    h = projekt_hinweise(projekt, wissens_repo)

    assert h["heikel"] and "schaltregler" not in h["ohne_regeln"]


def test_html_traegt_marker_zitat_und_escaped(wissens_repo):
    projekt = {"name": "<böse>", "positionen": [
        {"referenz": "C1", "klasse": "abblock_c"},
        {"referenz": "U2", "klasse": "schaltregler"},
    ]}

    html_text = baue_anleitung(projekt, wissens_repo, heute="2026-09-11")

    assert "⚠ VERMUTUNG" in html_text and "BELEGT" in html_text
    assert "<blockquote>" in html_text and "Original quote." in html_text
    assert "&lt;böse&gt;" in html_text and "<böse>" not in html_text
    assert "Stand 2026-09-11" in html_text
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** → **Step 4:** grün → **Step 5: Commit** `E6: Routing-Anleitung aus der Wissensbasis (Regeln je Klasse, Referenzen, Heikel, Stufen)`

---

### Task 5: Orchestrator + Router-Endpunkte

**Files:** Create `backend/app/kicad/export.py`; Modify `backend/app/routers/projekte.py`; Test `backend/tests/test_kicad_export_endpunkt.py`

**Interfaces — Produces:**
- `export.run_export(projekt: dict, wissens_repo: Path, ausgabe_basis: Path, symbols_dir: Path = Path("/usr/share/kicad/symbols"), heute: str = "") -> dict`:
  `{"ordner": str, "schaltplan": str, "pcb": str | None, "anleitung": str, "report": {"uebernommen": int, "uebersprungen": [{"referenz","bezeichnung","grund"}], "warnungen": [str], "pcb_hinweis": str | None}}`
  — slug aus Projektname (Regex `[^A-Za-z0-9._-]+` → `-`, wie alter project_slug); schreibt `<slug>.kicad_sch` (write_schematic), `<slug>.kicad_pcb` nur wenn `pcbnew_available()` (sonst `pcb=None`, `pcb_hinweis="pcbnew (KiCad-Python) nicht gefunden — Schaltplan und Anleitung wurden erzeugt."`; von build_pcb übersprungene Footprint-lose → warnungen), `anleitung.html` immer. Bei leerem Modell (alle unmapped) trotzdem Anleitung + Report, `schaltplan=None`? Nein — Spec: Report statt stilles Fehlen; Entscheidung: bei 0 Instanzen KEIN Schaltplan (`schaltplan=None`), Report erklärt es.
- Router: `POST /projekte/{id}/kicad-export` → obiges camelCased (`pcbHinweis`); `GET /projekte/{id}/kicad-anleitung` → `FileResponse(anleitung.html, media_type="text/html")`, 404 mit „Noch kein Export — erst KiCad-Export ausführen." wenn Datei fehlt; `POST /projekte/{id}/kicad-oeffnen` → versucht `xdg-open <schaltplan>` (subprocess.Popen, kein Warten), Meldung `"KiCad-Öffnen angestoßen: {pfad}"` bzw. 400 „Noch kein Export…"/„xdg-open nicht verfügbar". Ausgabe-Basis: env `HARDWARE_COPILOT_EXPORTE`, Default `~/hardware-copilot-exporte`; `WISSENSSCHICHT_REPO` wie gehabt.

- [ ] **Step 1: Failing Tests** (TestClient-App mit projekte-Router; Fixture: BESTAND_DB + Projekt mit 2 Positionen (C1 Device:C mit pins, R7 ohne Symbol), tmp WISSENSSCHICHT_REPO mit einer abblock_c-Regel, tmp HARDWARE_COPILOT_EXPORTE via monkeypatch):

```python
def test_export_erzeugt_artefakte_und_report(client, tmp_path):
    r = client.post("/projekte/1/kicad-export")

    assert r.status_code == 200
    daten = r.json()
    assert daten["schaltplan"].endswith(".kicad_sch")
    assert Path(daten["schaltplan"]).exists()
    assert Path(daten["anleitung"]).exists()
    assert daten["report"]["uebernommen"] == 1
    assert daten["report"]["uebersprungen"][0]["referenz"] == "R7"


def test_anleitung_endpoint_liefert_html(client):
    client.post("/projekte/1/kicad-export")

    r = client.get("/projekte/1/kicad-anleitung")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Routing-Anleitung" in r.text


def test_anleitung_vor_export_404(client):
    assert client.get("/projekte/1/kicad-anleitung").status_code == 404


def test_export_unbekanntes_projekt_404(client):
    assert client.post("/projekte/9/kicad-export").status_code == 404
```

- [ ] **Step 2: rot** → **Step 3: Implementierung** (heute via `date.today().isoformat()` NUR im Router beim Aufruf — Orchestrator bleibt injizierbar) → **Step 4:** alle Suiten grün → **Step 5: Commit** `E6: KiCad-Export-Orchestrator + Endpunkte (Export, Anleitung, Öffnen)`

---

### Task 6: Export-UI im Projekt-Tab

**Files:** Modify `src/components/panels/ProjektePanel.tsx`, `src/api/projekte.ts`, `src/types/projekte.ts`; Test an `src/components/panels/ProjektePanel.test.tsx` anfügen

**Interfaces / Verhalten (bindend):**
- api: `kicadExport(projektId): Promise<KicadExportErgebnis>` (POST), `kicadOeffnen(projektId): Promise<{meldung: string}>`, `anleitungUrl(projektId): string` (= `${API_BASE_URL}/projekte/${id}/kicad-anleitung`); Typ `KicadExportErgebnis {ordner, schaltplan: string|null, pcb: string|null, anleitung, report: {uebernommen, uebersprungen: {referenz, bezeichnung, grund}[], warnungen: string[], pcbHinweis: string|null}}`.
- Panel: unter der BOM-Tabelle Abschnitt „KiCad" (nur wenn Positionen > 0): Knopf „KiCad-Export" (während des Laufs disabled, Text „exportiere …"); nach Erfolg Report-Box: `✓ {uebernommen} Symbole` (grün), je übersprungene Zeile `⚠ {referenz} — {grund}` (gelb), Warnungen gedämpft, pcbHinweis gedämpft, Pfad `{ordner}` monospace; Knöpfe „Anleitung ansehen" (`window.open(anleitungUrl(id), "_blank")`) und „In KiCad öffnen" (`kicadOeffnen` → Meldung in Statuszeile). Fehler → rote Statuszeile (bestehendes Muster).
- Test: Export-Knopf → mock liefert Ergebnis mit 1 übernommen + 1 übersprungen → Report-Box zeigt „R7" und den Grund; „Anleitung ansehen" ruft window.open mit der URL (Spy).

- [ ] Steps: Test rot → Implementierung → `npx vitest run` alle grün → `npm run build` grün → Commit `E6: Export-UI — Report, Anleitung ansehen, In KiCad öffnen`

---

### Task 7: Gate-Lauf E6 (Controller)

1. Gate-Setup: Gate-DB, Projekt per Dienst mit vollständigen Angaben (U1 `Battery_Management:MCP73831-2-OT` via parts.yaml-MPN falls vorhanden, sonst explizit; C1/C2 `Device:C` mit pins {1: VBUS/VBAT, 2: GND}, R1 `Device:R` mit pins, R7 ohne Symbol als Report-Fall; Baugruppen Lademanagement/Versorgung); echtes Wissens-Repo.
2. Stack + Browser: Export-Knopf im Projekt-Tab → Report sichtbar (übernommen + R7-Zeile) → Screenshot; „Anleitung ansehen"-URL direkt abrufen und Regel-/⚠-Gehalt prüfen.
3. Headless-Verifikation: `kicad-cli sch erc` auf der erzeugten .kicad_sch (Fehler-Verstöße = 0 erwartet, wie die portierten Tests), `.kicad_pcb` existiert und lädt via pcbnew (python3 -c), Anleitung enthält projektbezogene Regeln mit Stufe+Quelle.
4. Befund in `bestand/README.md` („Gate-Lauf E6"), Commit; Whole-Branch-Review (stärkstes Modell) über den E6-Bereich, Fixes, Push auf PR #9. KiCad-Öffnen mit Oberfläche = Gerätetest des Users.

---

## Self-Review (beim Schreiben)

- **Spec §3 abgedeckt:** 3.1 Portierung+Kaskade+Report ✓ T1/T2; 3.2 drei Artefakte ✓ T3 (pcb)/T1+T2 (sch)/T4 (Anleitung aus Wissensbasis mit Stufen/Quellen/Heikel)/T5 (Ordner, pcb-Hinweis); 3.3 Bedienung ✓ T5/T6 (Report, Pfad, Öffnen, Anleitung im Tab via window.open). §6: kein Auto-Routing ✓ (nur Platzierung).
- **Platzhalter:** Port-Tasks verweisen bewusst auf die Originaldateien (wörtliche Kopie ist die Spezifikation); neue Module mit Vollcode-Tests.
- **Typ-Konsistenz:** ExportModel-Felder T1=T2=T3; report-Schlüssel T5=T6 (camelCase pcbHinweis); `heute` injizierbar durchgängig.
- **Risiken benannt:** heikel.toml-Feldnamen (T4: vor Implementierung nachlesen), parts.yaml-Inhalt fürs Gate (T7: prüfen, sonst explizite Symbole).
