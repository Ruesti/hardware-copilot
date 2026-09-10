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


def test_kaputte_block_datei_gibt_503(client, tmp_path):
    d = tmp_path / "bloecke"
    d.mkdir(exist_ok=True)
    (d / "B-001.toml").write_text("titel = kaputt ohne Anfuehrungszeichen")

    r = client.get("/wissen/bloecke")

    assert r.status_code == 503
    assert "Blocks" in r.json()["detail"]


def test_kaputte_regel_datei_gibt_503(client, tmp_path):
    d = tmp_path / "regeln" / "schaltregler"
    (d / "R-002.toml").write_text("id = kaputt ohne Anfuehrungszeichen")

    r = client.get("/wissen/regeln")

    assert r.status_code == 503
    assert "fehlerhaft" in r.json()["detail"]
