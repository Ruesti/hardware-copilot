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
