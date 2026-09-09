"""Motor-Kern: SDK-Messages → neutrale Ereignisse; Rückfragen-Roundtrip."""
import asyncio
import json
import sys

import pytest
from claude_agent_sdk import ResultMessage

from backend.app.motor.claude_motor import (
    ClaudeMotor,
    _optionen,
    uebersetze_bloecke,
    werkzeug_anzeige,
    zusatz_server_aus_claude_config,
)


def test_werkzeug_anzeige_zerlegt_mcp_namen():
    assert werkzeug_anzeige("mcp__bestand__teil_suchen") == "bestand: teil_suchen"
    assert werkzeug_anzeige("WebSearch") == "WebSearch"


class FakeText:
    def __init__(self, text): self.text = text
class FakeToolUse:
    def __init__(self, id, name, input): self.id, self.name, self.input = id, name, input
class FakeToolResult:
    def __init__(self, tool_use_id, is_error): self.tool_use_id, self.is_error = tool_use_id, is_error


def test_uebersetze_bloecke_liefert_ereignisse():
    ereignisse = list(uebersetze_bloecke([
        FakeText("Hallo"),
        FakeToolUse("t1", "mcp__bestand__teil_suchen", {"suchbegriff": "100nF"}),
        FakeToolResult("t1", False),
    ], werkzeug_namen={}))

    assert ereignisse[0] == {"typ": "text_haeppchen", "text": "Hallo"}
    assert ereignisse[1]["typ"] == "werkzeug_gestartet"
    assert ereignisse[1]["anzeige"] == "bestand: teil_suchen"
    assert ereignisse[2] == {"typ": "werkzeug_fertig", "id": "t1",
                             "name": "mcp__bestand__teil_suchen", "fehler": False}


@pytest.mark.asyncio
async def test_rueckfrage_roundtrip_erlaubt():
    motor = ClaudeMotor(client_fabrik=lambda cb: None)

    async def frage_stellen():
        return await motor._can_use_tool("Bash", {"command": "ls"}, None)

    aufgabe = asyncio.create_task(frage_stellen())
    ereignis = await asyncio.wait_for(motor._queue.get(), timeout=2)
    assert ereignis["typ"] == "rueckfrage"
    assert ereignis["art"] == "werkzeug"

    await motor.rueckfrage_antworten(ereignis["id"], erlaubt=True, antwort=None)
    ergebnis = await asyncio.wait_for(aufgabe, timeout=2)
    assert type(ergebnis).__name__ == "PermissionResultAllow"


@pytest.mark.asyncio
async def test_rueckfrage_ablehnen_traegt_nachricht():
    motor = ClaudeMotor(client_fabrik=lambda cb: None)
    aufgabe = asyncio.create_task(motor._can_use_tool("Bash", {"command": "rm -rf"}, None))
    ereignis = await motor._queue.get()

    await motor.rueckfrage_antworten(ereignis["id"], erlaubt=False, antwort="zu riskant")
    ergebnis = await aufgabe
    assert type(ergebnis).__name__ == "PermissionResultDeny"
    assert "zu riskant" in ergebnis.message


@pytest.mark.asyncio
async def test_abbrechen_loest_offene_rueckfragen_auf():
    motor = ClaudeMotor(client_fabrik=lambda cb: None)
    aufgabe = asyncio.create_task(motor._can_use_tool("Bash", {"command": "ls"}, None))
    await motor._queue.get()

    await motor.abbrechen()
    ergebnis = await asyncio.wait_for(aufgabe, timeout=2)
    assert type(ergebnis).__name__ == "PermissionResultDeny"
    assert motor._offene_rueckfragen == {}


@pytest.mark.asyncio
async def test_rueckfrage_antworten_doppelt_ist_still():
    """Fix 4: eine zweite Antwort auf dieselbe (schon aufgelöste) Rückfrage-ID
    darf nicht mit KeyError/InvalidStateError crashen, sondern wird ignoriert
    — z. B. wenn der Client aus Versehen doppelt sendet, oder ein Nachzügler
    eintrifft, nachdem ``abbrechen()`` alle offenen Rückfragen schon abgeräumt
    hat."""
    motor = ClaudeMotor(client_fabrik=lambda cb: None)
    aufgabe = asyncio.create_task(motor._can_use_tool("Bash", {"command": "ls"}, None))
    ereignis = await motor._queue.get()

    await motor.rueckfrage_antworten(ereignis["id"], erlaubt=True, antwort=None)
    await asyncio.wait_for(aufgabe, timeout=2)

    # Zweite Antwort auf dieselbe ID: unbekannt (schon aus dem Dict entfernt) —
    # darf keine Exception werfen.
    await motor.rueckfrage_antworten(ereignis["id"], erlaubt=True, antwort=None)

    # Unbekannte ID von Anfang an: ebenfalls still.
    await motor.rueckfrage_antworten("nie-existiert", erlaubt=False, antwort=None)


class FakeSDKClientMitAbsturz:
    """Simuliert einen SDK-Client, dessen ``receive_response()`` beim
    Iterieren explodiert (z. B. Verbindungsabbruch mitten in der Antwort)."""

    async def connect(self):
        pass

    async def query(self, text):
        pass

    async def receive_response(self):
        raise RuntimeError("SDK-Verbindung abgebrochen")
        yield  # pragma: no cover — macht die Funktion zum Async-Generator

    async def interrupt(self):
        pass

    async def disconnect(self):
        pass


@pytest.mark.asyncio
async def test_uebersetzer_absturz_liefert_fertig_mit_motor_fehler():
    """Fix 3: stürzt der Übersetzer-Lauf ab, muss ``frage()`` trotzdem mit
    einem "fertig"-Ereignis terminieren (Spec §6: der Chat muss den Abbruch
    melden statt für immer zu hängen)."""
    motor = ClaudeMotor(client_fabrik=lambda cb: FakeSDKClientMitAbsturz())
    await motor.start()

    ereignisse = [e async for e in motor.frage("Hallo")]

    assert len(ereignisse) == 1
    letztes = ereignisse[-1]
    assert letztes["typ"] == "fertig"
    assert "Motor-Fehler" in letztes["fehler"]
    assert "SDK-Verbindung abgebrochen" in letztes["fehler"]
    assert letztes["kosten_usd"] is None


# --- Konnect-Discovery (E4-Follow-up 1, Teil A) ---------------------------


def test_zusatz_server_findet_konnect(tmp_path):
    cfg = tmp_path / "claude.json"
    cfg.write_text(json.dumps({"mcpServers": {
        "Konnect-KiCad": {"command": "npx", "args": ["konnect"], "env": {"K": "1"}},
        "wissensschicht": {"command": "python", "args": ["-m", "wissensschicht.server"]},
        "remote": {"type": "http", "url": "https://x"},
    }}))

    gefunden = zusatz_server_aus_claude_config(cfg)

    assert list(gefunden) == ["Konnect-KiCad"]
    assert gefunden["Konnect-KiCad"]["command"] == "npx"


def test_zusatz_server_fehlende_config_ist_leer(tmp_path):
    assert zusatz_server_aus_claude_config(tmp_path / "gibtsnicht.json") == {}


def test_zusatz_server_kaputtes_json_ist_leer(tmp_path):
    cfg = tmp_path / "claude.json"
    cfg.write_text("{kaputt")

    assert zusatz_server_aus_claude_config(cfg) == {}


def test_zusatz_server_env_erweitert_namen(tmp_path, monkeypatch):
    monkeypatch.setenv("MOTOR_ZUSATZ_SERVER", "spezial")
    cfg = tmp_path / "claude.json"
    cfg.write_text(json.dumps({"mcpServers": {
        "spezial-werkzeug": {"command": "foo"}}}))

    assert "spezial-werkzeug" in zusatz_server_aus_claude_config(cfg)


def test_zusatz_server_fehlende_args_und_env_werden_ergaenzt(tmp_path):
    cfg = tmp_path / "claude.json"
    cfg.write_text(json.dumps({"mcpServers": {
        "konnect": {"command": "npx"}}}))

    gefunden = zusatz_server_aus_claude_config(cfg)

    assert gefunden["konnect"] == {"command": "npx", "args": [], "env": {}}


def test_optionen_traegt_konnect_in_allowed_tools():
    zusatz = {"Konnect-KiCad": {"command": "npx", "args": [], "env": {}}}

    optionen = _optionen(None, zusatz_server=zusatz)

    assert "mcp__Konnect-KiCad__*" in optionen.allowed_tools
    assert "mcp__bestand__*" in optionen.allowed_tools
    assert "mcp__wissensschicht__*" in optionen.allowed_tools
    assert "Konnect-KiCad" in optionen.mcp_servers
    assert "Konnect" in optionen.system_prompt
    assert "Zusätzlich verfügbar" in optionen.system_prompt


def test_optionen_ohne_zusatz_server_hat_nur_basis():
    optionen = _optionen(None, zusatz_server={})

    assert optionen.allowed_tools == ["mcp__bestand__*", "mcp__wissensschicht__*"]
    assert set(optionen.mcp_servers) == {"bestand", "wissensschicht"}
    assert "Zusätzlich verfügbar" not in optionen.system_prompt


def test_optionen_basis_gewinnt_bei_namenskollision():
    zusatz = {"bestand": {"command": "boese-uebernahme", "args": [], "env": {}}}

    optionen = _optionen(None, zusatz_server=zusatz)

    assert optionen.mcp_servers["bestand"]["command"] == sys.executable
    # keine doppelte allowed_tools-Zeile für den kollidierenden Namen
    assert optionen.allowed_tools.count("mcp__bestand__*") == 1


# --- Queue turn-scoped (E4-Follow-up 1, Teil B) ---------------------------


class FakeSDKClientEinTurn:
    """Simuliert einen SDK-Client, dessen ``receive_response()`` sofort mit
    einem ResultMessage-artigen Objekt endet (kein Text, keine Werkzeuge) —
    genug, damit ``_uebersetzer_lauf`` sofort ein "fertig" pusht."""

    def __init__(self):
        self.abgefragt = []

    async def connect(self):
        pass

    async def query(self, text):
        self.abgefragt.append(text)

    async def receive_response(self):
        nachricht = ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id="s1",
            total_cost_usd=0.01,
        )
        yield nachricht

    async def interrupt(self):
        pass

    async def disconnect(self):
        pass


@pytest.mark.asyncio
async def test_frage_bindet_queue_pro_turn_neu():
    """Bricht ein Konsument die Iteration eines Turns vorzeitig ab, darf ein
    Alt-Ereignis aus der alten Queue im nächsten Turn nicht mehr auftauchen —
    ``frage()`` muss ``self._queue`` zu Beginn jedes Turns neu binden."""
    motor = ClaudeMotor(client_fabrik=lambda cb: FakeSDKClientEinTurn())
    await motor.start()

    # Alt-Ereignis aus einem (fiktiven) vorherigen, vorzeitig abgebrochenen
    # Turn liegt noch in der zu diesem Zeitpunkt aktuellen Queue.
    alte_queue = motor._queue
    await alte_queue.put({"typ": "text_haeppchen", "text": "LECK aus altem Turn"})

    ereignisse = [e async for e in motor.frage("Neue Frage")]

    assert motor._queue is not alte_queue
    assert len(ereignisse) == 1
    assert ereignisse[0]["typ"] == "fertig"
    assert all("LECK" not in str(e) for e in ereignisse)


@pytest.mark.asyncio
async def test_frage_antwort_liefert_answers_als_record():
    motor = ClaudeMotor(client_fabrik=lambda cb: None)
    eingabe = {"questions": [{"question": "Welche Farbe magst du?",
                              "options": [{"label": "Rot"}, {"label": "Blau"}]}]}
    aufgabe = asyncio.create_task(motor._can_use_tool("AskUserQuestion", eingabe, None))
    ereignis = await asyncio.wait_for(motor._queue.get(), timeout=2)
    assert ereignis["art"] == "frage"

    await motor.rueckfrage_antworten(ereignis["id"], erlaubt=True, antwort="Blau")
    ergebnis = await asyncio.wait_for(aufgabe, timeout=2)
    assert ergebnis.updated_input["answers"] == {"Welche Farbe magst du?": "Blau"}
