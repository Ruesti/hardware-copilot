"""Neutrale Motor-Schnittstelle: Wire-Format (Ereignis-Dicts) und Protokoll.

Diese Datei kennt kein einziges Claude-spezifisches Symbol. Jede
Motor-Implementierung — heute der ClaudeMotor, denkbar auch ein künftiger
Nicht-Claude-Motor — muss ausschließlich dieses Ereignis-Vokabular sprechen,
damit das Frontend unabhängig vom konkreten Motor bleibt.

Statt eines eigenen Ereignis-Datentyps nutzen wir schlichte dicts als
Wire-Format (leicht JSON-serialisierbar) plus Konstanten für die Ereignistypen.
"""
from __future__ import annotations

from typing import AsyncIterator, Protocol

# Ereignistypen (Wire-Format-Konstanten) — exakt diese fünf Werte im Feld "typ"
TEXT_HAEPPCHEN = "text_haeppchen"
WERKZEUG_GESTARTET = "werkzeug_gestartet"
WERKZEUG_FERTIG = "werkzeug_fertig"
RUECKFRAGE = "rueckfrage"
FERTIG = "fertig"


class Motor(Protocol):
    """Schnittstelle, die jede Chat-Motor-Implementierung erfüllen muss.

    Wire-Format der von ``frage()`` gelieferten Ereignis-Dicts:
      - {"typ": "text_haeppchen", "text": str}
      - {"typ": "werkzeug_gestartet", "id": str, "name": str, "anzeige": str}
      - {"typ": "werkzeug_fertig", "id": str, "name": str, "fehler": bool}
      - {"typ": "rueckfrage", "id": str, "art": "werkzeug" | "frage",
         "text": str, "optionen": list[str]}
      - {"typ": "fertig", "fehler": str | None, "kosten_usd": float | None}
    """

    async def start(self) -> None:
        """Baut die Verbindung zum Motor auf (z. B. SDK-Client verbinden)."""
        ...

    async def frage(self, text: str) -> AsyncIterator[dict]:
        """Stellt eine Frage und liefert Ereignis-Dicts bis inkl. "fertig"."""
        ...

    async def rueckfrage_antworten(
        self, rueckfrage_id: str, erlaubt: bool, antwort: str | None
    ) -> None:
        """Löst eine offene Rückfrage auf (Werkzeug-Freigabe oder Nutzerantwort)."""
        ...

    async def abbrechen(self) -> None:
        """Bricht die laufende Antwort ab."""
        ...

    async def stop(self) -> None:
        """Baut die Verbindung zum Motor wieder ab."""
        ...
