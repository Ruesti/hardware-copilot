"""Block-E-Heikel-Mechanik: heikel.toml laden, Auslöser prüfen (§0 E1/E2)."""
from wissensschicht.heikel import lade_heikel, pruefe_heikel


HEIKEL_TOML = """\
[[bereich]]
name = "netzspannung"
spannung_min_v = 50.0
unterdrueckt_regeln = true
regel_unterdrueckung_grund = "Kleinspannungs-Quellen."
frage = "Platine oder Modul?"
fundstelle = ""
fundstelle_hinweis = "Keine belegte Quelle."

[[bereich]]
name = "akku_laden"
klassen = ["akku_lader"]
unterdrueckt_regeln = false
frage = "Geschuetzte Zelle oder roh?"
fundstelle = "TP4056 S. 2"
fundstelle_hinweis = ""

[[bereich]]
name = "funk"
achsen_trigger = { antenne = "eigenentwurf" }
unterdrueckt_regeln = false
frage = "Eigenentwurf oder Modul?"
fundstelle = ""
fundstelle_hinweis = ""
"""


def repo_mit_heikel(tmp_path):
    (tmp_path / "heikel.toml").write_text(HEIKEL_TOML)
    return tmp_path


def test_laedt_bereiche(tmp_path):
    bereiche = lade_heikel(repo_mit_heikel(tmp_path))

    assert [b.name for b in bereiche] == ["netzspannung", "akku_laden", "funk"]
    assert bereiche[0].unterdrueckt_regeln is True


def test_fehlende_datei_ergibt_keine_bereiche(tmp_path):
    assert lade_heikel(tmp_path) == []


def test_spannungsschwelle_triggert(tmp_path):
    bereiche = lade_heikel(repo_mit_heikel(tmp_path))

    treffer = pruefe_heikel(bereiche, {"klasse": ["versorgung_eingang"], "spannung_v": 230})
    assert [b.name for b in treffer] == ["netzspannung"]

    assert pruefe_heikel(bereiche, {"klasse": ["versorgung_eingang"], "spannung_v": 12}) == []
    assert pruefe_heikel(bereiche, {"klasse": ["versorgung_eingang"]}) == []


def test_klassen_trigger(tmp_path):
    bereiche = lade_heikel(repo_mit_heikel(tmp_path))

    treffer = pruefe_heikel(bereiche, {"klasse": ["akku_lader", "abblock_c"]})

    assert [b.name for b in treffer] == ["akku_laden"]


def test_achsen_trigger(tmp_path):
    bereiche = lade_heikel(repo_mit_heikel(tmp_path))

    assert [b.name for b in pruefe_heikel(bereiche, {"klasse": ["mcu_wifi"], "antenne": "eigenentwurf"})] == ["funk"]
    assert pruefe_heikel(bereiche, {"klasse": ["mcu_wifi"], "antenne": "pcb_onboard"}) == []
