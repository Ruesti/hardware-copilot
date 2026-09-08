"""MCP-Layer: die sechs E1-Tools sind registriert und laufen gegen die DB."""
import asyncio

from bestand import server


def test_alle_sechs_tools_registriert():
    tools = asyncio.run(server.mcp.list_tools())

    namen = {t.name for t in tools}
    assert namen == {"teil_suchen", "teil_anlegen", "menge_aendern",
                     "alternative_vermerken", "preis_cachen", "fach_leuchten"}


def test_anlegen_und_suchen_gegen_konfigurierte_db(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))

    meldung = server.teil_anlegen("100nF X7R 0805", menge=250, fach="A/3")
    assert "[T-1]" in meldung

    assert "Fach A/3" in server.teil_suchen("100nF")


def test_bestandsfehler_wird_als_warnzeile_gemeldet(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))

    meldung = server.teil_suchen("T-99")

    assert meldung.startswith("⚠ ")
    assert "T-99" in meldung
