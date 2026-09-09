"""Motor-Kern: SDK-Messages → neutrale Ereignisse; Rückfragen-Roundtrip."""
import asyncio

import pytest

from backend.app.motor.claude_motor import ClaudeMotor, uebersetze_bloecke, werkzeug_anzeige


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
