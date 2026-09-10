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
