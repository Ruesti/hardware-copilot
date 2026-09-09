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
