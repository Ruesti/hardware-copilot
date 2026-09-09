"""Motor-Router: Verlauf, Dialog-Roundtrip, neustart — mit Fake-Motor."""
import asyncio

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.motor import router as motor_router


class FakeMotor:
    def __init__(self):
        self.rueckfragen = []
        self.gestoppt = False

    async def start(self):
        pass

    async def frage(self, text):
        yield {"typ": "text_haeppchen", "text": f"Echo: {text}"}
        yield {"typ": "fertig", "fehler": None, "kosten_usd": 0.01}

    async def rueckfrage_antworten(self, rueckfrage_id, erlaubt, antwort):
        self.rueckfragen.append((rueckfrage_id, erlaubt, antwort))

    async def abbrechen(self):
        pass

    async def stop(self):
        self.gestoppt = True


def test_dialog_und_verlauf(monkeypatch):
    monkeypatch.setattr(motor_router, "motor_fabrik", FakeMotor)
    motor_router.zustand_zuruecksetzen()
    client = TestClient(app)

    with client.websocket_connect("/motor/ws") as ws:
        assert ws.receive_json()["typ"] == "verlauf"
        ws.send_json({"typ": "nutzer", "text": "Hallo"})
        assert ws.receive_json() == {"typ": "text_haeppchen", "text": "Echo: Hallo"}
        assert ws.receive_json()["typ"] == "fertig"

    # Reconnect: Verlauf enthält Nutzer-Zeile + beide Ereignisse
    with client.websocket_connect("/motor/ws") as ws:
        verlauf = ws.receive_json()
        typen = [e["typ"] for e in verlauf["ereignisse"]]
        assert typen == ["nutzer", "text_haeppchen", "fertig"]


def test_neustart_leert_verlauf(monkeypatch):
    monkeypatch.setattr(motor_router, "motor_fabrik", FakeMotor)
    motor_router.zustand_zuruecksetzen()
    client = TestClient(app)

    with client.websocket_connect("/motor/ws") as ws:
        ws.receive_json()
        ws.send_json({"typ": "nutzer", "text": "eins"})
        ws.receive_json(); ws.receive_json()
        ws.send_json({"typ": "neustart"})
        assert ws.receive_json() == {"typ": "verlauf", "ereignisse": []}


@pytest.mark.asyncio
async def test_motor_sicherstellen_erzeugt_unter_parallellast_nur_einen(monkeypatch):
    """Race-Regressionstest: parallele _motor_sicherstellen()-Aufrufe dürfen
    nur einen Motor erzeugen — sonst leakt der unterlegene Kandidat seine
    gestartete SDK-Session (nie gestoppt, da nie in _motor landet)."""
    erzeugt = []

    class LangsamerFake(FakeMotor):
        def __init__(self):
            super().__init__()
            erzeugt.append(self)

        async def start(self):
            await asyncio.sleep(0.05)

    monkeypatch.setattr(motor_router, "motor_fabrik", LangsamerFake)
    motor_router.zustand_zuruecksetzen()

    a, b = await asyncio.gather(
        motor_router._motor_sicherstellen(), motor_router._motor_sicherstellen()
    )
    assert a is True
    assert b is True
    assert len(erzeugt) == 1
