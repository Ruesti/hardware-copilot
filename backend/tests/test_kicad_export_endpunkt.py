"""Export-Orchestrator + Router-Endpunkte (E6 Task 5): Export, Anleitung, Öffnen.

Fixture-Aufbau wie `test_projekte_router.py` (BESTAND_DB über monkeypatch,
`ProjektDienst` mit injiziertem `heute`), ergänzt um ein tmp-Wissensrepo mit
einer `abblock_c`-Regel (Template aus `test_kicad_anleitung.py`) und ein tmp
`HARDWARE_COPILOT_EXPORTE`-Verzeichnis. Die Tests laufen den vollen Pfad —
echte KiCad-Symbole unter /usr/share/kicad/symbols, echtes pcbnew — und
erzeugen reale Dateien in `tmp_path`.
"""
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routers.projekte import router
from bestand.projekte import ProjektDienst
from bestand.service import BestandsDienst

R_002 = """\
id = "R-002"
bereich = "abblock_c"
aussage = "Testaussage Abblock-C."
begruendung = "Testbegründung Abblock-C."
staerke = "sollte"
stufe = "vermutung"
datum_eintrag = 2026-09-08
datum_geprueft = 2026-09-08
ausnahmen = []

[quelle]
typ = "keine"
titel = ""
dokument = ""
fundstelle = ""
url = ""
zitat = ""

[geltung]
klasse = "abblock_c"
"""


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))
    BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-11")
    p = ProjektDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-11")
    p.anlegen("Blink-Board")
    p.position_hinzufuegen(1, "C1", "100nF", klasse="abblock_c",
                           baugruppe="Versorgung", kicad_symbol="Device:C",
                           pins={"1": "GND", "2": "+3V3"})
    p.position_hinzufuegen(1, "R7", "10k")

    wissens_repo = tmp_path / "wissen"
    (wissens_repo / "regeln" / "abblock_c").mkdir(parents=True)
    (wissens_repo / "regeln" / "abblock_c" / "R-002.toml").write_text(R_002)
    monkeypatch.setenv("WISSENSSCHICHT_REPO", str(wissens_repo))
    monkeypatch.setenv("HARDWARE_COPILOT_EXPORTE", str(tmp_path / "exporte"))

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


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


def test_export_camelcase_und_pcb_hinweis_feld(client):
    """pcbnew ist in dieser Umgebung installiert — `pcb` wird erzeugt, C1 hat
    aber kein Footprint (kein teil_id → keine Bibliotheks-Herkunft) und
    landet als Warnung; `pcbHinweis` ist dann None (nicht 400/Fehler)."""
    daten = client.post("/projekte/1/kicad-export").json()

    assert "pcbHinweis" in daten["report"]
    assert daten["report"]["pcbHinweis"] is None
    assert daten["pcb"] is not None and Path(daten["pcb"]).exists()
    assert any("C1" in w for w in daten["report"]["warnungen"])


def test_oeffnen_vor_export_400(client):
    r = client.post("/projekte/1/kicad-oeffnen")
    assert r.status_code == 400
    assert "Noch kein Export" in r.json()["detail"]


def test_oeffnen_nach_export_stoesst_an(client):
    client.post("/projekte/1/kicad-export")

    r = client.post("/projekte/1/kicad-oeffnen")
    assert r.status_code == 200
    assert "KiCad-Öffnen angestoßen" in r.json()["meldung"]


def test_oeffnen_unbekanntes_projekt_404(client):
    assert client.post("/projekte/9/kicad-oeffnen").status_code == 404


def test_leeres_modell_ohne_schaltplan_aber_mit_anleitung(client, tmp_path):
    """Zweites Projekt nur mit R7 (ohne Symbol) — alle Positionen unabgebildet:
    kein Schaltplan/PCB, aber die Anleitung entsteht trotzdem, Report erklärt."""
    p = ProjektDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-11")
    p.anlegen("Nur-R7")
    p.position_hinzufuegen(2, "R7", "10k")

    daten = client.post("/projekte/2/kicad-export").json()

    assert daten["schaltplan"] is None
    assert daten["pcb"] is None
    assert Path(daten["anleitung"]).exists()
    assert daten["report"]["uebernommen"] == 0
    assert daten["report"]["uebersprungen"][0]["referenz"] == "R7"
