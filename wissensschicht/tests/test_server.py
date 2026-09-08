"""MCP-Layer: die fünf Phase-2-Tools sind registriert und rufen den Dienst auf."""
import asyncio

from wissensschicht import server


def test_alle_phase2_tools_registriert():
    tools = asyncio.run(server.mcp.list_tools())

    namen = {t.name for t in tools}
    assert namen == {"query_rules", "get_rule", "check_hint", "report_gap", "list_gaps"}


def test_get_rule_laeuft_gegen_konfiguriertes_repo(tmp_path, monkeypatch):
    from .test_store import BELEGT, schreibe
    schreibe(tmp_path, "schaltregler", "R-001", BELEGT)
    monkeypatch.setenv("WISSENSSCHICHT_REPO", str(tmp_path))

    text = server.get_rule("R-001")

    assert "Stufe: BELEGT" in text
