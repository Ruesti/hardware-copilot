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
