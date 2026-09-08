"""C2-Prüfung: Modell schlägt Stufen vor, der Server darf nur abstufen, nie hochstufen."""
import pytest

from wissensschicht.checker import check_hint, UnbekannteRegel
from .test_matching import regel


REGELN = {r.id: r for r in [
    regel("R-005", "schaltregler", stufe="belegt"),
    regel("R-008", "schaltregler", stufe="vermutung"),
]}


def test_regelteil_wird_auf_gespeicherte_stufe_abgestuft():
    ergebnis = check_hint(REGELN, "R-008", regel_stufe="belegt", anwendung_stufe="vermutung")

    assert ergebnis.regel_stufe == "vermutung"
    assert any("R-008" in k and "abgestuft" in k for k in ergebnis.korrekturen)


def test_freiwillig_niedrigere_behauptung_bleibt():
    ergebnis = check_hint(REGELN, "R-005", regel_stufe="vermutung", anwendung_stufe="vermutung")

    assert ergebnis.regel_stufe == "vermutung"


def test_anwendungsteil_wird_immer_auf_vermutung_gedeckelt():
    ergebnis = check_hint(REGELN, "R-005", regel_stufe="belegt", anwendung_stufe="belegt")

    assert ergebnis.anwendung_stufe == "vermutung"
    assert any("Anwendung" in k for k in ergebnis.korrekturen)


def test_korrekte_behauptung_bleibt_ohne_korrekturen():
    ergebnis = check_hint(REGELN, "R-005", regel_stufe="belegt", anwendung_stufe="vermutung")

    assert ergebnis.regel_stufe == "belegt"
    assert ergebnis.anwendung_stufe == "vermutung"
    assert ergebnis.korrekturen == []


def test_unbekannte_regel_id_ist_fehler():
    with pytest.raises(UnbekannteRegel, match="R-999"):
        check_hint(REGELN, "R-999", regel_stufe="belegt", anwendung_stufe="vermutung")
