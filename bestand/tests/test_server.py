"""MCP-Layer: die sechs E1-Tools sind registriert und laufen gegen die DB."""
import asyncio

from bestand import server


def test_alle_sechs_tools_registriert():
    tools = asyncio.run(server.mcp.list_tools())

    namen = {t.name for t in tools}
    assert {"teil_suchen", "teil_anlegen", "menge_aendern",
            "alternative_vermerken", "preis_cachen", "fach_leuchten"} <= namen


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


def test_projekt_tools_registriert():
    tools = asyncio.run(server.mcp.list_tools())

    namen = {t.name for t in tools}
    assert {"projekt_anlegen", "position_hinzufuegen", "position_verknuepfen",
            "projekt_zeigen", "projekt_abbuchen"} <= namen


def test_projekt_rundlauf_ueber_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))
    server.teil_anlegen("100nF", menge=10, fach="A/1")

    assert "[P-1]" in server.projekt_anlegen("Blink-Board")
    server.position_hinzufuegen(1, "C1", "100nF", menge=2, teil_id=1,
                                baugruppe="Versorgung", pins={"1": "GND"})
    text = server.projekt_zeigen(1)
    assert "1 von 1 im Bestand" in text and "Versorgung" in text

    assert "abgebucht" in server.projekt_abbuchen(1)
    assert "Menge 8" in server.teil_suchen("T-1")


def test_projekt_fehler_als_warnzeile(tmp_path, monkeypatch):
    monkeypatch.setenv("BESTAND_DB", str(tmp_path / "bestand.db"))

    assert server.projekt_zeigen(9).startswith("⚠ ")
