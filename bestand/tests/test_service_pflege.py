"""Dienst: Menge relativ ändern, Alternativen und Preise (mit Datum) vermerken."""
import pytest

from bestand.service import BestandsDienst, BestandsFehler


@pytest.fixture
def dienst(tmp_path):
    d = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08")
    d.anlegen("100nF X7R 0805", menge=10, fach="A/3")
    return d


def test_menge_aendern_ist_relativ_und_meldet_neuen_stand(dienst):
    assert dienst.menge_aendern(1, +5) == "[T-1] Menge jetzt 15."
    assert dienst.menge_aendern(1, -12) == "[T-1] Menge jetzt 3."


def test_menge_darf_nicht_unter_null(dienst):
    with pytest.raises(BestandsFehler, match="Bestand: 10"):
        dienst.menge_aendern(1, -11)


def test_menge_aendern_unbekanntes_teil(dienst):
    with pytest.raises(BestandsFehler, match="T-99"):
        dienst.menge_aendern(99, +1)


def test_alternative_erscheint_im_detail(dienst):
    dienst.alternative_vermerken(1, "GRM21BR71H104KA01",
                                 hersteller_nr="Murata", hinweis="gleiches Gehäuse")

    assert "GRM21BR71H104KA01 (Murata) — gleiches Gehäuse (vermerkt 2026-09-08)" \
        in dienst.suchen("T-1")


def test_preis_erscheint_im_detail_mit_stand_vom(dienst):
    meldung = dienst.preis_cachen(1, "LCSC", 0.02, url="https://lcsc.com/x")

    assert "Stand vom 2026-09-08" in meldung
    assert "0.02 € bei LCSC — Stand vom 2026-09-08" in dienst.suchen("T-1")


def test_preis_null_oder_negativ_ist_fehler(dienst):
    with pytest.raises(BestandsFehler, match="Preis"):
        dienst.preis_cachen(1, "LCSC", 0)


def test_menge_darf_exakt_auf_null(dienst):
    assert dienst.menge_aendern(1, -10) == "[T-1] Menge jetzt 0."
