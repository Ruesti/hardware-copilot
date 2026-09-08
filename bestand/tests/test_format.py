"""Ausgabeformate: Kurzzeile fürs Suchergebnis, Markdown-Detail mit Preis-Datum."""
from bestand.format import detail, kurzzeile

TEIL = {"id": 3, "bezeichnung": "100nF X7R 0805", "menge": 250,
        "klasse": "abblock_c", "fach": "A/3", "hersteller_nr": "CL21B104KBCNNNC",
        "eckdaten": "50 V, X7R, 0805", "datenblatt_url": "https://example.com/db.pdf"}


def test_kurzzeile_nennt_id_menge_und_fach():
    zeile = kurzzeile(TEIL)

    assert zeile == "[T-3] 100nF X7R 0805 — Menge 250, Fach A/3, Klasse abblock_c"


def test_kurzzeile_ohne_fach_sagt_das_offen():
    teil = dict(TEIL, fach=None)

    assert "kein Fach zugewiesen" in kurzzeile(teil)


def test_detail_zeigt_preis_nur_mit_stand_vom_datum():
    text = detail(TEIL, alternativen=[], preise=[
        {"quelle": "LCSC", "preis_eur": 0.02, "url": "https://lcsc.com/x",
         "datum": "2026-09-08"}])

    assert "### [T-3] 100nF X7R 0805" in text
    assert "0.02 € bei LCSC — Stand vom 2026-09-08" in text


def test_detail_benennt_leere_abschnitte_statt_sie_wegzulassen():
    text = detail(TEIL, alternativen=[], preise=[])

    assert "Alternativen: keine vermerkt" in text
    assert "Preise: keine im Cache" in text


def test_detail_listet_alternative_mit_datum():
    text = detail(TEIL, alternativen=[
        {"bezeichnung": "GRM21BR71H104KA01", "hersteller_nr": "Murata",
         "hinweis": "gleiches Gehäuse", "datum": "2026-09-08"}], preise=[])

    assert "- GRM21BR71H104KA01 (Murata) — gleiches Gehäuse (vermerkt 2026-09-08)" in text
