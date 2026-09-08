"""Matching: Geltungs-Bedingungsfelder einer Regel gegen einen beschriebenen Fall prüfen."""
from wissensschicht.matching import match_rules
from wissensschicht.store import Regel


def regel(rid, klasse, stufe="belegt", **geltung_extra):
    return Regel(
        id=rid, bereich="test", aussage=f"Aussage {rid}", begruendung="B",
        staerke="sollte", stufe=stufe,
        datum_eintrag="2026-09-08", datum_geprueft="2026-09-08",
        ausnahmen=[],
        quelle={"typ": "datenblatt", "titel": "T", "dokument": "D",
                "fundstelle": "S. 1", "url": "u", "zitat": "Z"}
        if stufe == "belegt" else
        {"typ": "keine", "titel": "", "dokument": "", "fundstelle": "", "url": "", "zitat": ""},
        geltung={"klasse": klasse, **geltung_extra},
    )


def test_klasse_entscheidet_ueber_treffer():
    regeln = [regel("R-001", "schaltregler"), regel("R-002", "mcu_wifi")]

    treffer = match_rules(regeln, {"klasse": ["mcu_wifi"]})

    assert [t.regel.id for t in treffer] == ["R-002"]


def test_mehrere_fallklassen_treffen_mehrere_regeln():
    regeln = [regel("R-001", "schaltregler"), regel("R-002", "mcu_wifi"),
              regel("R-003", "versorgung_eingang")]

    treffer = match_rules(regeln, {"klasse": ["schaltregler", "versorgung_eingang"]})

    assert sorted(t.regel.id for t in treffer) == ["R-001", "R-003"]


def test_zusatzachse_muss_uebereinstimmen_wenn_angegeben():
    regeln = [regel("R-001", "motortreiber_stepper", last_typ="induktiv")]

    assert match_rules(regeln, {"klasse": ["motortreiber_stepper"], "last_typ": "induktiv"})
    assert not match_rules(regeln, {"klasse": ["motortreiber_stepper"], "last_typ": "ohmsch"})


def test_fehlende_fallangabe_trifft_aber_meldet_unbestaetigt():
    regeln = [regel("R-001", "mcu_wifi", antenne="pcb_onboard")]

    treffer = match_rules(regeln, {"klasse": ["mcu_wifi"]})

    assert len(treffer) == 1
    assert treffer[0].unbestaetigt == ["antenne=pcb_onboard"]


def test_vollstaendig_bestaetigter_treffer_hat_keine_unbestaetigten():
    regeln = [regel("R-001", "mcu_wifi", antenne="pcb_onboard")]

    treffer = match_rules(regeln, {"klasse": ["mcu_wifi"], "antenne": "pcb_onboard"})

    assert treffer[0].unbestaetigt == []
