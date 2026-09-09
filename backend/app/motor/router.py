"""Motor-WebSocket-Router: Verlauf, Dialog, Rückfragen, Neustart.

Bindet die neutrale Motor-Schnittstelle (schnittstelle.py) über einen einzigen
WS-Endpunkt `/motor/ws` ans Frontend — ein Motor pro Prozess, lazily beim
ersten Connect erzeugt (nie beim Import dieses Moduls, damit Tests
``motor_fabrik`` durch einen Fake ersetzen können, bevor überhaupt ein
Motor entsteht). Läuft nur auf 127.0.0.1 wie das ganze Backend (Single-User-
Desktop) — keine zusätzliche Auth nötig.
"""
from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .claude_motor import ClaudeMotor

router = APIRouter()

# Modul-Fabrik — in Tests durch einen FakeMotor ersetzt (motor_router.motor_fabrik = ...)
motor_fabrik = ClaudeMotor

# Modulzustand: ein Motor, der Sitzungs-Verlauf und die verbundenen Clients.
_motor: Any = None
_verlauf: list[dict] = []
_clients: set[WebSocket] = set()
_laufende_frage: asyncio.Task | None = None
# Schützt die Erzeugung+Start des Motors vor Doppel-Erzeugung bei parallelen
# Aufrufen (z. B. gleichzeitiger Connect mehrerer Clients).
_motor_lock: asyncio.Lock = asyncio.Lock()


def zustand_zuruecksetzen() -> None:
    """Setzt den kompletten Modulzustand zurück — nur für Tests.

    Das Lock wird dabei neu angelegt statt nur freigegeben: ``asyncio.Lock``
    bindet sich (je nach Python-Version) an den Event-Loop seiner ersten
    Verwendung, und TestClient-Läufe können unterschiedliche Loops
    benutzen. Ein neues Lock vermeidet Kollisionen zwischen Testläufen.
    """
    global _motor, _verlauf, _clients, _laufende_frage, _motor_lock
    _motor = None
    _verlauf = []
    _clients = set()
    _laufende_frage = None
    _motor_lock = asyncio.Lock()


async def _sende_an_alle(ereignis: dict) -> None:
    """Hängt ein Ereignis an den Verlauf und schickt es an alle verbundenen Clients.

    Sende-Fehler (z. B. weil ein Client schon weg ist) werden pro Client
    abgefangen und entfernen ihn aus ``_clients`` — ein toter Client darf den
    Versand an die übrigen nicht stören.
    """
    _verlauf.append(ereignis)
    for client in list(_clients):
        try:
            await client.send_json(ereignis)
        except Exception:
            _clients.discard(client)


async def _sende_verlauf_an_alle() -> None:
    """Schickt den (frischen) Verlaufs-Snapshot an alle verbundenen Clients.

    Anders als ``_sende_an_alle``: das Verlaufs-Ereignis selbst landet nicht
    im Verlauf — es ist eine Momentaufnahme, kein Dialog-Schritt.
    """
    ereignis = {"typ": "verlauf", "ereignisse": list(_verlauf)}
    for client in list(_clients):
        try:
            await client.send_json(ereignis)
        except Exception:
            _clients.discard(client)


async def _motor_sicherstellen() -> bool:
    """Erzeugt und startet den Motor, falls noch keiner existiert.

    Erzeugung+Start laufen unter ``_motor_lock`` mit Double-Check-Locking:
    ohne das Lock könnten zwei parallele Aufrufe (z. B. gleichzeitiger
    Connect zweier Clients) je einen Motor erzeugen und starten — der
    unterlegene würde nie gestoppt und leakt seine gestartete SDK-Session.

    Bei Startfehler geht ein "fertig"-Ereignis mit Fehlertext über
    ``_sende_an_alle`` an Verlauf und alle Clients (nicht nur an den
    übergebenen Empfänger — sonst zeigt ein Reconnect eine unbeantwortete
    Frage); der Motor bleibt ``None``, damit ein späterer Versuch erneut
    starten kann.
    """
    global _motor
    if _motor is not None:
        return True
    async with _motor_lock:
        if _motor is not None:
            return True
        kandidat = motor_fabrik()
        try:
            await kandidat.start()
        except Exception as e:
            with contextlib.suppress(Exception):
                await _sende_an_alle(
                    {"typ": "fertig", "fehler": str(e), "kosten_usd": None}
                )
            return False
        _motor = kandidat
        return True


async def _frage_ausfuehren(text: str) -> None:
    """Stellt die Frage am Motor und verteilt jedes Ereignis an alle Clients."""
    try:
        async for ereignis in _motor.frage(text):
            await _sende_an_alle(ereignis)
    except Exception as e:
        await _sende_an_alle({"typ": "fertig", "fehler": str(e), "kosten_usd": None})


async def _neustart() -> None:
    """Bricht eine laufende Frage ab, stoppt den Motor, leert den Verlauf,
    erzeugt per Fabrik einen neuen Motor und verteilt den leeren Verlauf."""
    global _motor, _verlauf, _laufende_frage

    if _laufende_frage is not None and not _laufende_frage.done():
        _laufende_frage.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _laufende_frage
    _laufende_frage = None

    if _motor is not None:
        await _motor.stop()
        _motor = None

    _verlauf = []
    await _motor_sicherstellen()
    await _sende_verlauf_an_alle()


@router.websocket("/motor/ws")
async def motor_ws(websocket: WebSocket) -> None:
    global _laufende_frage

    await websocket.accept()
    _clients.add(websocket)
    try:
        await websocket.send_json({"typ": "verlauf", "ereignisse": list(_verlauf)})
        await _motor_sicherstellen()

        while True:
            nachricht = await websocket.receive_json()
            typ = nachricht.get("typ")

            if typ == "nutzer":
                if _laufende_frage is not None and not _laufende_frage.done():
                    await websocket.send_json(
                        {"typ": "fertig", "fehler": "beschäftigt — bitte warten"}
                    )
                    continue
                text = nachricht.get("text", "")
                _verlauf.append({"typ": "nutzer", "text": text})
                if not await _motor_sicherstellen():
                    continue
                _laufende_frage = asyncio.create_task(_frage_ausfuehren(text))

            elif typ == "rueckfrage_antwort":
                if _motor is not None:
                    await _motor.rueckfrage_antworten(
                        nachricht.get("id"),
                        nachricht.get("erlaubt"),
                        nachricht.get("antwort"),
                    )

            elif typ == "abbrechen":
                if _motor is not None:
                    await _motor.abbrechen()

            elif typ == "neustart":
                await _neustart()

    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(websocket)
