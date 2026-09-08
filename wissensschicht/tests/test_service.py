"""Dienst-Schicht: was die MCP-Tools tatsächlich tun (ohne Transport)."""
import pytest

from wissensschicht.service import WissensDienst
from .test_store import BELEGT, VERMUTUNG, schreibe


@pytest.fixture
def repo(tmp_path):
    schreibe(tmp_path, "schaltregler", "R-001", BELEGT, klasse="schaltregler")
    schreibe(tmp_path, "motortreiber", "R-002", VERMUTUNG, klasse="motortreiber_stepper")
    return tmp_path


def test_query_liefert_kurzformen_fuer_treffende_klassen(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["schaltregler"])

    assert "R-001" in antwort
    assert "BELEGT" in antwort
    assert "R-002" not in antwort


def test_query_vermutung_traegt_marker(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["motortreiber_stepper"], achsen={"last_typ": "induktiv"})

    assert "⚠ VERMUTUNG" in antwort


def test_query_ohne_treffer_benennt_luecke_und_protokolliert(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["ldo"], frage="Dropout-Reserve für LDO?")

    assert "Keine belegte Regel" in antwort
    eintraege = dienst.luecken()
    assert len(eintraege) == 1
    assert eintraege[0]["frage"] == "Dropout-Reserve für LDO?"


def test_query_ohne_treffer_ohne_frage_protokolliert_nicht(repo):
    dienst = WissensDienst(repo)

    antwort = dienst.query(klassen=["ldo"])

    assert "Keine belegte Regel" in antwort
    assert dienst.luecken() == []


def test_regel_liefert_volltext_mit_json(repo):
    dienst = WissensDienst(repo)

    text = dienst.regel("R-001")

    assert "Stufe: BELEGT" in text
    assert "```json" in text


def test_regel_unbekannt_gibt_klare_meldung(repo):
    dienst = WissensDienst(repo)

    text = dienst.regel("R-999")

    assert "R-999" in text
    assert "existiert nicht" in text


def test_pruefe_deckelt_anwendungsteil(repo):
    dienst = WissensDienst(repo)

    text = dienst.pruefe("R-001", regel_stufe="belegt", anwendung_stufe="belegt")

    assert "vermutung" in text
    assert "abgestuft" in text
