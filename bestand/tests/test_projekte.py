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
