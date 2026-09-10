"""Dienst: Teil anlegen (mit Fach-Auto-Anlage) und zweistufig suchen."""
import pytest

from bestand.service import BestandsDienst, BestandsFehler


@pytest.fixture
def dienst(tmp_path):
    return BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08")


def test_anlegen_meldet_id_menge_und_fach(dienst):
    meldung = dienst.anlegen("100nF X7R 0805", menge=250, fach="A/3",
                             klasse="abblock_c")

    assert meldung == "[T-1] 100nF X7R 0805 angelegt — Menge 250, Fach A/3."


def test_anlegen_legt_unbekanntes_fach_automatisch_an(dienst):
    dienst.anlegen("Teil eins", menge=1, fach="B/7")
    dienst.anlegen("Teil zwei", menge=1, fach="B/7")

    assert "Fach B/7" in dienst.suchen("Teil eins")


def test_anlegen_lehnt_fach_ohne_schraegstrich_ab(dienst):
    with pytest.raises(BestandsFehler, match="Regal/Position"):
        dienst.anlegen("X", menge=1, fach="A3")


def test_suchen_findet_ueber_teilstring_und_liefert_kurzzeilen(dienst):
    dienst.anlegen("100nF X7R 0805", menge=250, fach="A/3", klasse="abblock_c")
    dienst.anlegen("10uF Elko", menge=40, fach="A/4")

    treffer = dienst.suchen("100nF")

    assert "[T-1] 100nF X7R 0805 — Menge 250, Fach A/3" in treffer
    assert "10uF" not in treffer


def test_suchen_filtert_optional_nach_klasse(dienst):
    dienst.anlegen("100nF X7R", menge=1, fach="A/3", klasse="abblock_c")
    dienst.anlegen("100nF Folie", menge=1, fach="A/5", klasse="")

    treffer = dienst.suchen("100nF", klasse="abblock_c")

    assert "X7R" in treffer and "Folie" not in treffer


def test_suchen_mit_t_id_liefert_detail(dienst):
    dienst.anlegen("100nF X7R 0805", menge=250, fach="A/3",
                   hersteller_nr="CL21B104KBCNNNC")

    text = dienst.suchen("T-1")

    assert text.startswith("### [T-1] 100nF X7R 0805")
    assert "Hersteller-Nr: CL21B104KBCNNNC" in text


def test_suchen_ohne_treffer_benennt_das_offen(dienst):
    meldung = dienst.suchen("gibtsnicht")

    assert "Kein Teil gefunden" in meldung
    assert "teil_anlegen" in meldung


def test_unbekannte_t_id_ist_fehler(dienst):
    with pytest.raises(BestandsFehler, match="T-99"):
        dienst.suchen("T-99")


def test_anlegen_lehnt_negative_menge_ab(dienst):
    with pytest.raises(BestandsFehler, match="Menge"):
        dienst.anlegen("X", menge=-1, fach="A/3")


def test_suchen_strippt_leerraum(dienst):
    dienst.anlegen("100nF X7R 0805", menge=1, fach="A/3")

    assert "[T-1]" in dienst.suchen("  100nF ")


def test_suchen_mit_leerem_begriff_wird_abgelehnt(dienst):
    assert "Suchbegriff ist leer" in dienst.suchen("   ")


def test_suchen_behandelt_prozent_und_unterstrich_woertlich(dienst):
    dienst.anlegen("Poti 10% Toleranz", menge=1, fach="A/3")
    dienst.anlegen("Poti 20k linear", menge=1, fach="A/4")

    treffer = dienst.suchen("10%")

    assert "Toleranz" in treffer and "linear" not in treffer


def test_suchen_unterstrich_ist_kein_wildcard(dienst):
    dienst.anlegen("A_B literal underscore", menge=1, fach="A/3")
    dienst.anlegen("AXB single char instead", menge=1, fach="A/4")

    treffer = dienst.suchen("A_B")

    assert "A_B literal underscore" in treffer
    assert "AXB single char instead" not in treffer
