"""MCP-Layer: die fünf Phase-2-Tools sind registriert und rufen den Dienst auf."""
import asyncio

from wissensschicht import server


def test_alle_tools_registriert():
    tools = asyncio.run(server.mcp.list_tools())

    namen = {t.name for t in tools}
    assert namen == {"query_rules", "get_rule", "check_hint", "report_gap", "list_gaps",
                     "record_block", "search_blocks", "get_block"}


def test_record_und_search_block_laufen_gegen_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("WISSENSSCHICHT_REPO", str(tmp_path))
    from .test_blocks import DATEN

    meldung = server.record_block(**DATEN)
    assert "B-001" in meldung

    treffer = server.search_blocks("xc6220")
    assert "B-001" in treffer
    assert "Vermutung" in server.get_block("B-001")


def test_get_rule_laeuft_gegen_konfiguriertes_repo(tmp_path, monkeypatch):
    from .test_store import BELEGT, schreibe
    schreibe(tmp_path, "schaltregler", "R-001", BELEGT)
    monkeypatch.setenv("WISSENSSCHICHT_REPO", str(tmp_path))

    text = server.get_rule("R-001")

    assert "Stufe: BELEGT" in text
