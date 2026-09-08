"""Store: Regeln aus TOML-Verzeichnis laden und validieren."""
import pytest

from wissensschicht.store import load_rules, StoreError


BELEGT = """\
id = "{rid}"
bereich = "{bereich}"
aussage = "Testaussage."
begruendung = "Testbegründung."
staerke = "sollte"
stufe = "belegt"
datum_eintrag = 2026-09-08
datum_geprueft = 2026-09-08
ausnahmen = ["Ausnahme eins"]

[quelle]
typ = "datenblatt"
titel = "Testblatt"
dokument = "DOC1"
fundstelle = "PDF-S. 1"
url = "https://example.com/doc.pdf"
zitat = "Original quote."

[geltung]
klasse = "{klasse}"
"""

VERMUTUNG = """\
id = "{rid}"
bereich = "{bereich}"
aussage = "Vermutete Aussage."
begruendung = "Erfahrung."
staerke = "kann"
stufe = "vermutung"
datum_eintrag = 2026-09-08
datum_geprueft = 2026-09-08
ausnahmen = []

[quelle]
typ = "keine"
titel = ""
dokument = ""
fundstelle = ""
url = ""
zitat = ""

[geltung]
klasse = "{klasse}"
last_typ = "induktiv"
"""


def schreibe(basis, bereich, rid, vorlage, klasse="schaltregler"):
    d = basis / "regeln" / bereich
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{rid}.toml").write_text(vorlage.format(rid=rid, bereich=bereich, klasse=klasse))


def test_laedt_alle_regeln_aus_verzeichnis(tmp_path):
    schreibe(tmp_path, "schaltregler", "R-001", BELEGT)
    schreibe(tmp_path, "motortreiber", "R-002", VERMUTUNG, klasse="motortreiber_stepper")

    regeln = load_rules(tmp_path)

    assert sorted(r.id for r in regeln) == ["R-001", "R-002"]
    r1 = next(r for r in regeln if r.id == "R-001")
    assert r1.stufe == "belegt"
    assert r1.quelle["typ"] == "datenblatt"
    assert r1.geltung["klasse"] == "schaltregler"
    assert r1.ausnahmen == ["Ausnahme eins"]


def test_belegt_ohne_zitat_wird_abgelehnt(tmp_path):
    kaputt = BELEGT.replace('zitat = "Original quote."', 'zitat = ""')
    schreibe(tmp_path, "schaltregler", "R-001", kaputt)

    with pytest.raises(StoreError, match="R-001"):
        load_rules(tmp_path)


def test_vermutung_mit_primaerquellentyp_wird_abgelehnt(tmp_path):
    kaputt = VERMUTUNG.replace('typ = "keine"', 'typ = "datenblatt"')
    schreibe(tmp_path, "schaltregler", "R-001", kaputt)

    with pytest.raises(StoreError, match="R-001"):
        load_rules(tmp_path)


def test_ungueltige_stufe_wird_abgelehnt(tmp_path):
    kaputt = BELEGT.replace('stufe = "belegt"', 'stufe = "bewiesen"')
    schreibe(tmp_path, "schaltregler", "R-001", kaputt)

    with pytest.raises(StoreError, match="R-001"):
        load_rules(tmp_path)


def test_doppelte_id_wird_abgelehnt(tmp_path):
    schreibe(tmp_path, "schaltregler", "R-001", BELEGT)
    d = tmp_path / "regeln" / "esp32"
    d.mkdir(parents=True)
    (d / "R-001.toml").write_text(BELEGT.format(rid="R-001", bereich="esp32", klasse="mcu_wifi"))

    with pytest.raises(StoreError, match="R-001"):
        load_rules(tmp_path)
