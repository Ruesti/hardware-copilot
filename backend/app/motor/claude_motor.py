"""Claude-Motor: verbindet die neutrale Motor-Schnittstelle mit dem claude-agent-sdk.

Claude-Code-spezifischer Code — SDK-Importe, Options-Aufbau, Message-Übersetzung —
lebt ausschließlich in dieser Datei. ``schnittstelle.py`` bleibt Claude-frei, damit
ein künftiger Nicht-Claude-Motor dieselbe Schnittstelle bedienen könnte.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
)

from backend.app.motor.schnittstelle import (
    FERTIG,
    RUECKFRAGE,
    TEXT_HAEPPCHEN,
    WERKZEUG_FERTIG,
    WERKZEUG_GESTARTET,
)

SYSTEM_PROMPT = (
    "Du bist der Elektronik-Werkstatt-Kopilot im Hardware-Copilot-Cockpit. "
    "Dir stehen zwei Werkzeuggruppen zur Verfügung: 'bestand' für die "
    "Bauteile-Datenbank (Teile suchen/anlegen, Menge ändern, Alternativen "
    "vermerken, Preise cachen, Fach beleuchten) und 'wissensschicht' für "
    "Regel-Blöcke und die Wissenssuche (Regeln abfragen, Regel-Details, "
    "Hinweis-Stufen prüfen, Lücken melden/auflisten, Blöcke aufzeichnen/"
    "suchen). Gib Regel-Blöcke aus der Wissensschicht wörtlich wieder, "
    "stufe ihre Sicherheitsstufe niemals hoch und entferne den Hinweis "
    "'⚠ VERMUTUNG' niemals. Antworte kompakt und auf Deutsch."
)


def werkzeug_anzeige(name: str) -> str:
    """Wandelt einen Werkzeugnamen in eine kompakte Anzeige um.

    MCP-Namen der Form ``mcp__<server>__<tool>`` werden zu ``"<server>: <tool>"``;
    alle anderen Namen (z. B. eingebaute Werkzeuge wie ``WebSearch``) bleiben
    unverändert.
    """
    teile = name.split("__")
    if len(teile) == 3 and teile[0] == "mcp":
        _, server, werkzeug = teile
        return f"{server}: {werkzeug}"
    return name


def _kompakte_eingabe(eingabe: dict[str, Any]) -> str:
    """Kurze, lesbare Darstellung eines Werkzeug-Inputs für Rückfrage-Texte."""
    return ", ".join(f"{schluessel}={wert!r}" for schluessel, wert in eingabe.items())


def _frage_aus_eingabe(eingabe: dict[str, Any]) -> tuple[str, list[str]]:
    """Liest Fragetext und Options-Labels aus dem Input von ``AskUserQuestion``.

    Das Frage-Werkzeug ist ein CLI-seitiges Bordwerkzeug ohne eigenen Typ im
    Python-SDK; sein Input folgt der Form
    ``{"questions": [{"question": str, "options": [{"label": str, ...}, ...]}]}``.
    Nur die erste Frage wird abgebildet — mehrere Rückfragen in einer Runde
    sind für das Cockpit-Wire-Format (eine Rückfrage pro Ereignis) nicht
    vorgesehen.
    """
    fragen = eingabe.get("questions") or []
    if not fragen:
        return _kompakte_eingabe(eingabe), []
    erste = fragen[0]
    text = erste.get("question", "")
    optionen = [
        option.get("label", str(option)) if isinstance(option, dict) else str(option)
        for option in erste.get("options", [])
    ]
    return text, optionen


def uebersetze_bloecke(bloecke, werkzeug_namen: dict[str, str]) -> list[dict]:
    """Übersetzt SDK-Content-Blöcke (Duck-Typing) in neutrale Ereignis-Dicts.

    Pure Funktion, ohne laufende SDK-Session testbar. Blöcke werden anhand
    ihrer Attribute erkannt, nicht anhand ihres Typs: ``text`` → Text,
    ``input`` → Werkzeugstart, ``tool_use_id`` → Werkzeugende. ``werkzeug_namen``
    bildet Werkzeug-IDs auf Namen ab; Werkzeugstart-Blöcke tragen dort ihren
    Namen ein, damit der zugehörige Werkzeugende-Block (der den Namen selbst
    nicht mitführt) ihn nachschlagen kann.
    """
    ereignisse: list[dict] = []
    for block in bloecke:
        if hasattr(block, "text"):
            ereignisse.append({"typ": TEXT_HAEPPCHEN, "text": block.text})
        elif hasattr(block, "input"):
            werkzeug_namen[block.id] = block.name
            ereignisse.append({
                "typ": WERKZEUG_GESTARTET,
                "id": block.id,
                "name": block.name,
                "anzeige": werkzeug_anzeige(block.name),
            })
        elif hasattr(block, "tool_use_id"):
            name = werkzeug_namen.get(block.tool_use_id, block.tool_use_id)
            ereignisse.append({
                "typ": WERKZEUG_FERTIG,
                "id": block.tool_use_id,
                "name": name,
                "fehler": bool(getattr(block, "is_error", False)),
            })
    return ereignisse


def zusatz_server_aus_claude_config(
    config_pfad: Path | None = None,
    namen: tuple[str, ...] | None = None,
) -> dict[str, dict]:
    """Übernimmt stdio-MCP-Server aus der Claude-Code-Config (user-Scope).

    Konnect (KiCad-Anbindung, Spec §3.5) ist maschinenabhängig registriert —
    auf dem Entwicklungs-NUC gar nicht, auf dem PC des Nutzers schon. Statt
    Konnect fest zu verdrahten, lesen wir dieselbe Config, die auch die
    Claude-Code-CLI selbst nutzt (``~/.claude.json``, user-Scope-Server unter
    dem Top-Level-Schlüssel ``mcpServers``) und übernehmen, was zum
    Namensfilter passt.

    Standard-Namen: ``("konnect",)`` plus alle in ``MOTOR_ZUSATZ_SERVER``
    (kommagetrennt) genannten. Vergleich case-insensitiv als Teilstring des
    Servernamens — z. B. matcht "konnect" sowohl "konnect" als auch
    "Konnect-KiCad". Nur stdio-Einträge (die einen "command"-Schlüssel
    tragen) werden übernommen; http/sse-Einträge (Remote-MCP) werden
    übersprungen, da ``mcp_servers`` in ``ClaudeAgentOptions`` dafür ein
    anderes Eintragsformat braucht als hier gebaut wird.

    Fehlt die Config-Datei, ist sie kein gültiges JSON oder ihr Wurzelwert
    kein Dict, liefert die Funktion ein leeres Dict — nie eine Exception.
    Das hält ``_optionen()`` netz-/dateisystemtolerant: eine kaputte oder
    fehlende Config darf den Motor nicht am Start hindern.
    """
    pfad = config_pfad if config_pfad is not None else Path.home() / ".claude.json"
    if namen is None:
        env_namen = tuple(
            n.strip().lower()
            for n in os.environ.get("MOTOR_ZUSATZ_SERVER", "").split(",")
            if n.strip()
        )
        namen = ("konnect",) + env_namen

    try:
        rohdaten = json.loads(pfad.read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(rohdaten, dict):
        return {}
    server = rohdaten.get("mcpServers")
    if not isinstance(server, dict):
        return {}

    treffer: dict[str, dict] = {}
    for name, eintrag in server.items():
        if not isinstance(eintrag, dict) or "command" not in eintrag:
            continue  # kein stdio-Eintrag (z. B. http/sse) oder kaputter Eintrag
        if not any(gesucht in name.lower() for gesucht in namen):
            continue
        treffer[name] = {
            "command": eintrag["command"],
            "args": eintrag.get("args", []),
            "env": eintrag.get("env", {}),
        }
    return treffer


def _optionen(
    rueckfrage_callback, zusatz_server: dict[str, dict] | None = None
) -> ClaudeAgentOptions:
    """Baut die ClaudeAgentOptions für die Cockpit-Werkstatt-Session.

    Bindet die beiden Basis-MCP-Server (bestand, wissensschicht) als Stdio-
    Prozesse im selben venv ein und erlaubt per Wildcard alle ihre Werkzeuge,
    ohne andere Werkzeuge (Bash, WebSearch, …) automatisch freizugeben — die
    laufen weiter über ``can_use_tool``.

    ``zusatz_server`` (Default: Discovery aus ``~/.claude.json``, siehe
    ``zusatz_server_aus_claude_config``) kommt bewusst als optionaler
    Parameter statt fest verdrahteter Discovery — so bleibt ``_optionen()``
    ohne Netz/Session/echte Config testbar (Tests reichen ein festes Dict
    ein) und trotzdem ist der Produktionspfad (kein Argument) die echte
    Discovery. Bei Namenskollision mit den Basis-Servern gewinnt die Basis
    (kein Überschreiben von bestand/wissensschicht durch einen gleichnamigen
    Zusatz-Server).
    """
    if zusatz_server is None:
        zusatz_server = zusatz_server_aus_claude_config()

    repo = str(Path(__file__).resolve().parents[3])
    umgebung = {"PYTHONPATH": repo}
    basis = {
        "bestand": {
            "command": sys.executable,
            "args": ["-m", "bestand.server"],
            "env": {
                **umgebung,
                "BESTAND_DB": os.environ.get(
                    "BESTAND_DB", str(Path.home() / ".hardware-copilot/bestand.db")
                ),
            },
        },
        "wissensschicht": {
            "command": sys.executable,
            "args": ["-m", "wissensschicht.server"],
            "env": {
                **umgebung,
                "WISSENSSCHICHT_REPO": os.environ.get(
                    "WISSENSSCHICHT_REPO", str(Path.home() / "projects/hardware-wissen")
                ),
            },
        },
    }
    # Basis zuletzt gemischt, damit sie bei Namenskollision gewinnt.
    mcp_servers = {**zusatz_server, **basis}
    # Nur echte Zusatz-Namen (keine Kollisionen mit der Basis) bekommen eine
    # eigene allowed_tools-Zeile — die Basis-Server haben ihre schon unten.
    zusatz_namen = [name for name in zusatz_server if name not in basis]

    system_prompt = SYSTEM_PROMPT
    if zusatz_namen:
        system_prompt += f" Zusätzlich verfügbar: {', '.join(zusatz_namen)}."
        if any("konnect" in name.lower() for name in zusatz_namen):
            system_prompt += " Nutze Konnect für KiCad-Schaltplan-Arbeit."

    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        cwd=repo,
        permission_mode="default",
        can_use_tool=rueckfrage_callback,
        mcp_servers=mcp_servers,
        # Wildcard-Suffix "__*" ist die vom SDK verifizierte Form, um alle
        # Werkzeuge eines MCP-Servers freizugeben (siehe Report: SDK-Realität
        # vs. Brief — der Brief-Entwurf ohne "__*" hätte keine Wirkung gehabt).
        # Empirisch verifiziert 2026-09-09: Rauchtest mit echter SDK-Session
        # (teil_suchen über mcp__bestand__teil_suchen) löste keine Rückfrage
        # aus und lieferte den echten Bestandstreffer; das SDK selbst warnt
        # zudem, dass ein solcher allowed_tools-Eintrag can_use_tool umgeht.
        allowed_tools=["mcp__bestand__*", "mcp__wissensschicht__*"]
        + [f"mcp__{name}__*" for name in zusatz_namen],
    )


class ClaudeMotor:
    """Claude-Code-gestützter Motor: implementiert die Motor-Schnittstelle."""

    def __init__(self, client_fabrik: Callable[[Callable], Any] | None = None) -> None:
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._offene_rueckfragen: dict[str, dict[str, Any]] = {}
        self._client_fabrik = client_fabrik or (
            lambda rueckfrage_callback: ClaudeSDKClient(
                options=_optionen(rueckfrage_callback)
            )
        )
        self._client = self._client_fabrik(self._can_use_tool)

    async def start(self) -> None:
        """Verbindet den SDK-Client (das Äquivalent zum Context-Manager-Eintritt)."""
        await self._client.connect()

    async def frage(self, text: str) -> AsyncIterator[dict]:
        """Stellt eine Frage und liefert Ereignis-Dicts bis inkl. "fertig".

        Übersetzer-Task und Rückfrage-Callback laufen nebenläufig und pushen
        beide in dieselbe Queue; ``frage()`` liest sie nur noch aus, damit
        Rückfragen (die mitten in der Antwort auftauchen können) nicht auf
        das Ende der Übersetzung warten müssen.

        Turn-scoped Queue: ``self._queue`` wird hier bei jedem Aufruf neu
        gebunden statt (wie ursprünglich) einmalig in ``__init__``. Grund:
        bricht ein Konsument die Iteration dieses Async-Generators vorzeitig
        ab (z. B. ein WS-Client trennt die Verbindung mitten in der Antwort),
        bleiben in der alten Queue u. U. noch ungelesene Ereignisse aus
        diesem abgebrochenen Turn liegen. Ohne Neubindung würden sie beim
        nächsten ``frage()``-Aufruf als vermeintliche Ereignisse *dieses*
        neuen Turns ausgelesen — ein Leck über Turn-Grenzen hinweg.
        Die alte Queue bleibt dabei niemandes Problem: der zugehörige
        Übersetzer-Task des vorigen Turns wird im ``finally`` unten schon vor
        Rückkehr aus dem vorigen ``frage()``-Aufruf gecancelt und awaited,
        ist zum Zeitpunkt des nächsten Aufrufs also bereits beendet. Sollte
        er (in einer Rennlage) doch noch einmal in die alte Queue schreiben,
        landet das Ereignis in einem Objekt, auf das niemand mehr referenziert
        — harmlos, es wird einfach nie gelesen und vom GC eingesammelt.
        """
        self._queue = asyncio.Queue()
        await self._client.query(text)
        uebersetzer = asyncio.create_task(self._uebersetzer_lauf())
        try:
            while True:
                ereignis = await self._queue.get()
                yield ereignis
                if ereignis["typ"] == FERTIG:
                    break
        finally:
            uebersetzer.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await uebersetzer

    async def _uebersetzer_lauf(self) -> None:
        """Liest SDK-Messages und pusht übersetzte Ereignisse in die Queue.

        Ein Absturz beim Iterieren (z. B. SDK-Verbindungsfehler) darf
        ``frage()`` nicht für immer hängen lassen — die dortige Queue-Schleife
        wartet sonst ewig auf ein "fertig"-Ereignis, das nie kommt. Deshalb
        fängt dieser Rumpf jede Exception ab und legt selbst ein "fertig" mit
        Fehlertext in die Queue (Spec §6: Abbruch muss sich im Chat melden).
        """
        werkzeug_namen: dict[str, str] = {}
        try:
            async for message in self._client.receive_response():
                if isinstance(message, ResultMessage):
                    fehler = None if message.subtype == "success" else message.subtype
                    await self._queue.put({
                        "typ": FERTIG,
                        "fehler": fehler,
                        "kosten_usd": message.total_cost_usd,
                    })
                    continue
                inhalt = getattr(message, "content", None)
                if isinstance(inhalt, list):
                    for ereignis in uebersetze_bloecke(inhalt, werkzeug_namen):
                        await self._queue.put(ereignis)
        except Exception as e:
            await self._queue.put({
                "typ": FERTIG,
                "fehler": f"Motor-Fehler: {e}",
                "kosten_usd": None,
            })

    async def _can_use_tool(self, werkzeug_name: str, eingabe: dict, kontext: Any):
        """Permission-Callback: stellt eine Rückfrage und wartet auf die Antwort."""
        rueckfrage_id = str(uuid.uuid4())
        future: asyncio.Future = asyncio.get_running_loop().create_future()

        if werkzeug_name == "AskUserQuestion":
            art = "frage"
            text, optionen = _frage_aus_eingabe(eingabe)
        else:
            art = "werkzeug"
            anzeige = werkzeug_anzeige(werkzeug_name)
            eingabe_text = _kompakte_eingabe(eingabe)
            text = f"{anzeige} {eingabe_text}".strip() if eingabe_text else anzeige
            optionen = []

        self._offene_rueckfragen[rueckfrage_id] = {
            "future": future,
            "art": art,
            "eingabe": eingabe,
        }
        await self._queue.put({
            "typ": RUECKFRAGE,
            "id": rueckfrage_id,
            "art": art,
            "text": text,
            "optionen": optionen,
        })
        return await future

    async def rueckfrage_antworten(
        self, rueckfrage_id: str, erlaubt: bool, antwort: str | None
    ) -> None:
        """Löst eine offene Rückfrage auf und setzt das wartende Future.

        Unbekannte oder schon beantwortete IDs (z. B. eine doppelt beim
        Client eingehende Antwort, oder ein Nachzügler nach ``abbrechen()``,
        das alle offenen Rückfragen bereits abgeräumt hat) werden still
        ignoriert statt mit ``KeyError``/``InvalidStateError`` zu crashen.
        """
        eintrag = self._offene_rueckfragen.pop(rueckfrage_id, None)
        if eintrag is None:
            return
        future = eintrag["future"]
        if future.done():
            return
        if not erlaubt:
            future.set_result(
                PermissionResultDeny(message=antwort or "Vom Nutzer abgelehnt")
            )
            return
        aktualisierte_eingabe = None
        if eintrag["art"] == "frage" and antwort:
            aktualisierte_eingabe = {**eintrag["eingabe"], "answers": antwort}
        future.set_result(PermissionResultAllow(updated_input=aktualisierte_eingabe))

    def _offene_rueckfragen_abraeumen(self, grund: str) -> None:
        """Löst alle noch offenen Rückfragen-Futures ab und leert das Dict.

        Verhindert, dass ``rueckfrage_antworten()`` nie aufgerufen wird und
        die wartenden ``_can_use_tool``-Coroutinen (und damit die SDK-Antwort)
        bei Abbruch oder Sitzungsende für immer hängen bleiben.
        """
        for eintrag in self._offene_rueckfragen.values():
            future = eintrag["future"]
            if not future.done():
                future.set_result(PermissionResultDeny(message=grund))
        self._offene_rueckfragen.clear()

    async def abbrechen(self) -> None:
        """Bricht die laufende Antwort ab."""
        self._offene_rueckfragen_abraeumen("Vom Nutzer abgebrochen")
        if self._client is not None:
            await self._client.interrupt()

    async def stop(self) -> None:
        """Trennt den SDK-Client (das Äquivalent zum Context-Manager-Austritt)."""
        self._offene_rueckfragen_abraeumen("Sitzung beendet")
        await self._client.disconnect()
