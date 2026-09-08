"""Service-Integration der Heikel-Mechanik plus Katalog-Validierung (§0 E, GRENZEN.md 5/6)."""
import pytest

from wissensschicht.service import WissensDienst
from .test_heikel import HEIKEL_TOML
from .test_store import BELEGT, VERMUTUNG, schreibe


@pytest.fixture
def repo(tmp_path):
    schreibe(tmp_path, "versorgung", "R-001", BELEGT, klasse="versorgung_eingang")
    schreibe(tmp_path, "akku-laden", "R-002", BELEGT, klasse="akku_lader")
    schreibe(tmp_path, "motortreiber", "R-003", VERMUTUNG, klasse="motortreiber_stepper")
    (tmp_path / "heikel.toml").write_text(HEIKEL_TOML)
    return tmp_path


def test_netzspannung_stellt_frage_und_unterdrueckt_regeln(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["versorgung_eingang"], achsen={"spannung_v": 230})

    assert "HEIKLER BEREICH" in antwort
    assert "Platine oder Modul?" in antwort
    assert "Keine belegte Quelle." in antwort
    assert "R-001" not in antwort
    assert "Kleinspannungs-Quellen." in antwort


def test_akku_stellt_frage_vor_den_regeln(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["akku_lader"])

    assert "HEIKLER BEREICH" in antwort
    assert "Geschuetzte Zelle oder roh?" in antwort
    assert "TP4056 S. 2" in antwort
    assert "R-002" in antwort
    assert antwort.index("Geschuetzte Zelle oder roh?") < antwort.index("R-002")


def test_unbekannte_klasse_wird_gemeldet_statt_leerlauf(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["netz_230v"])

    assert "Unbekannte Klasse" in antwort
    assert "netz_230v" in antwort
    assert "akku_lader" in antwort  # bekannte Klassen werden genannt
    assert dienst.luecken() == []   # Tippfehler erzeugen keine Lücken-Einträge


def test_unbekannter_achsenwert_warnt(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["motortreiber_stepper"], achsen={"last_typ": "induktiiv"})

    assert "induktiiv" in antwort
    assert "unbekannt" in antwort.lower()


def test_numerische_fallachsen_loesen_keine_warnung_aus(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["akku_lader"], achsen={"spannung_v": 4.2, "strom_a": 0.5})

    assert "unbekannt" not in antwort.lower()


def test_leeres_ergebnis_wird_auch_ohne_frage_protokolliert(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["motortreiber_stepper"], achsen={"last_typ": "ohmsch"})

    assert "Keine belegte Regel" in antwort
    eintraege = dienst.luecken()
    assert len(eintraege) == 1
    assert "motortreiber_stepper" in eintraege[0]["frage"]
