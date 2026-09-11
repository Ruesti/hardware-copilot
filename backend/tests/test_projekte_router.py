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
