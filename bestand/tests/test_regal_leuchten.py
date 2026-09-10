"""fach_leuchten: ohne Regal Auskunft, mit Regal HTTP-Befehl, Ausfall bleibt nützlich."""
import pytest

from bestand.service import BestandsDienst, BestandsFehler


def dienst_mit(tmp_path, **kw):
    d = BestandsDienst(tmp_path / "bestand.db", heute=lambda: "2026-09-08", **kw)
    d.anlegen("100nF X7R 0805", menge=10, fach="A/3")
    return d


def test_ohne_regal_url_kommt_fach_auskunft(tmp_path):
    d = dienst_mit(tmp_path)

    meldung = d.fach_leuchten(1)

    assert meldung == ("Kein Regal konfiguriert (BESTAND_REGAL_URL) — "
                       "[T-1] liegt in Fach A/3.")


def test_mit_regal_url_wird_befehl_gesendet(tmp_path):
    gesendet = {}
    d = dienst_mit(tmp_path, regal_url="http://regal.local/leuchten",
                   sender=lambda url, befehl: gesendet.update(url=url, **befehl))

    meldung = d.fach_leuchten(1, farbe="blau", dauer_s=10)

    assert gesendet == {"url": "http://regal.local/leuchten", "led": None,
                        "regal": "A", "position": "3", "farbe": "blau",
                        "dauer_s": 10}
    assert meldung == "Fach A/3 leuchtet blau (10 s) — [T-1] 100nF X7R 0805."


def test_regal_nicht_erreichbar_nennt_trotzdem_das_fach(tmp_path):
    def kaputt(url, befehl):
        raise OSError("connection refused")
    d = dienst_mit(tmp_path, regal_url="http://regal.local/leuchten", sender=kaputt)

    with pytest.raises(BestandsFehler, match=r"nicht erreichbar.*Fach A/3"):
        d.fach_leuchten(1)


def test_teil_ohne_fach_ist_fehler(tmp_path):
    d = dienst_mit(tmp_path)
    d._conn.execute("UPDATE teile SET fach_id = NULL WHERE id = 1")

    with pytest.raises(BestandsFehler, match="kein Fach"):
        d.fach_leuchten(1)
