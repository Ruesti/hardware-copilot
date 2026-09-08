"""C6-Lückenprotokoll: unbeantwortete Fragen landen in luecken.md des Wissens-Repos."""
from wissensschicht.gaps import report_gap, list_gaps


KOPF = (
    "# Lücken-Protokoll (C6)\n\n"
    "| Datum | Frage/Thema | Warum offen | Status |\n"
    "|---|---|---|---|\n"
)


def test_luecke_wird_angehaengt_und_wieder_gelistet(tmp_path):
    pfad = tmp_path / "luecken.md"
    pfad.write_text(KOPF + "| 2026-09-08 | IPC-2152 | kostenpflichtig | offen |\n")

    report_gap(pfad, frage="USB-ESD-Schutz", grund="keine Regel vorhanden", datum="2026-09-09")
    eintraege = list_gaps(pfad)

    assert len(eintraege) == 2
    assert eintraege[1]["frage"] == "USB-ESD-Schutz"
    assert eintraege[1]["status"] == "offen"


def test_list_gaps_liest_bestehende_eintraege(tmp_path):
    pfad = tmp_path / "luecken.md"
    pfad.write_text(KOPF + "| 2026-09-08 | IPC-2152 | kostenpflichtig | offen |\n")

    eintraege = list_gaps(pfad)

    assert eintraege == [{"datum": "2026-09-08", "frage": "IPC-2152",
                          "grund": "kostenpflichtig", "status": "offen"}]


def test_report_gap_legt_datei_mit_kopf_an_wenn_sie_fehlt(tmp_path):
    pfad = tmp_path / "luecken.md"

    report_gap(pfad, frage="Neu", grund="Test", datum="2026-09-09")

    assert pfad.exists()
    assert "| Datum |" in pfad.read_text()
    assert list_gaps(pfad)[0]["frage"] == "Neu"
